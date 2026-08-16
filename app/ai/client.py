"""
Cliente HTTP hacia el LLM local. Única puerta de salida al modelo — ningún
otro módulo hace requests contra el servidor de IA (DRY).

Usa la API **OpenAI-compatible** (`/v1/chat/completions`, `/v1/embeddings`,
`/v1/models`) en vez de la API nativa de Ollama (`/api/generate`) porque ese
subconjunto lo exponen tanto Ollama como LM Studio de forma prácticamente
idéntica — el mismo cliente funciona apuntando a cualquiera de los dos, solo
cambia `OLLAMA_HOST`/`OLLAMA_MODEL` en `.env`. En este entorno de desarrollo
se usa LM Studio (`http://localhost:1234`); en producción/servidor,
`requirements.md` §5.2 define Ollama como el runtime.

Nota de compatibilidad: LM Studio exige `response_format` tipo `json_schema`
(con el schema completo) o `text` -- NO acepta el `json_object` "flojo" que
sí soporta Ollama. `generar()` intenta `json_schema` primero y, si el
servidor lo rechaza, cae a pedir el JSON solo por instrucciones del prompt
(que ya es lo que hace `prompts.construir_prompt_analisis`). Esto hace que
el cliente funcione contra cualquiera de los dos sin acoplarse a uno.
"""

import logging
from typing import Optional

import requests

from app.common.retry import reintentar_con_backoff
from app.config import get_settings

logger = logging.getLogger(__name__)

# Schema JSON que se le pide al modelo cuando el servidor soporta
# response_format=json_schema (LM Studio). Ollama ignora esto si no lo
# soporta -- generar() cae a modo texto en ese caso (ver _post_chat).
_ANALISIS_JSON_SCHEMA = {
    "name": "analisis_oferta",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "resumen": {"type": "string"},
            "requisitos": {"type": "array", "items": {"type": "string"}},
            "beneficios": {"type": "array", "items": {"type": "string"}},
            "seniority": {"type": ["string", "null"]},
            "empresa_real": {"type": ["string", "null"]},
            "score": {"type": "integer"},
            "score_razon": {"type": "string"},
        },
        "required": [
            "resumen",
            "requisitos",
            "beneficios",
            "seniority",
            "empresa_real",
            "score",
            "score_razon",
        ],
        "additionalProperties": False,
    },
}


class OllamaClient:
    """Cliente contra un servidor local con API OpenAI-compatible
    (Ollama o LM Studio, ver docstring del módulo)."""

    def __init__(
        self,
        host: Optional[str] = None,
        modelo: Optional[str] = None,
        modelo_embeddings: Optional[str] = None,
        timeout_segundos: Optional[int] = None,
    ):
        settings = get_settings()
        self.host = (host or settings.ollama_host).rstrip("/")
        self.modelo = modelo or settings.ollama_model
        self.modelo_embeddings = modelo_embeddings or settings.ollama_modelo_embeddings
        # Timeout generoso: la latencia está aceptada por diseño
        # (requirements.md §5.2), un 7B puede tardar decenas de segundos.
        self.timeout = timeout_segundos or settings.ollama_timeout_segundos

    def generar(self, prompt: str, formato_json: bool = True) -> str:
        """Manda el prompt al modelo y devuelve el texto crudo de la
        respuesta. NO parsea nada -- eso es responsabilidad de
        `app.ai.schemas.parsear_respuesta_llm`."""

        def _intento() -> str:
            return self._post_chat(prompt, formato_json)

        return reintentar_con_backoff(_intento, etiqueta="[ai.client]", logger=logger)

    def _post_chat(self, prompt: str, formato_json: bool) -> str:
        payload = {
            "model": self.modelo,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,  # análisis consistente, no creativo
        }
        if formato_json:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": _ANALISIS_JSON_SCHEMA,
            }

        response = requests.post(
            f"{self.host}/v1/chat/completions", json=payload, timeout=self.timeout
        )

        # Si el servidor no soporta json_schema (ej. una versión de Ollama
        # que solo acepta json_object o ninguno), reintenta sin forzar
        # formato -- el prompt ya pide JSON explícitamente por su cuenta.
        if response.status_code == 400 and formato_json:
            logger.info(
                "[ai.client] Servidor rechazó response_format=json_schema, "
                "reintentando sin forzar formato"
            )
            payload.pop("response_format", None)
            response = requests.post(
                f"{self.host}/v1/chat/completions", json=payload, timeout=self.timeout
            )

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def embeddings(self, texto: str) -> list[float]:
        """Vector de embedding de un texto corto (ver app/ai/embeddings.py
        para el dedup semántico -- NO se usa para descripciones completas)."""

        def _intento() -> list[float]:
            response = requests.post(
                f"{self.host}/v1/embeddings",
                json={"model": self.modelo_embeddings, "input": texto},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

        return reintentar_con_backoff(_intento, etiqueta="[ai.client.embeddings]", logger=logger)

    def esta_disponible(self) -> bool:
        """Ping liviano para el healthcheck del smoke test de CI
        (docs/design.md §4, Transversal). No usa reintentos -- un healthcheck
        debe fallar rápido, no colgar la corrida esperando backoffs."""
        try:
            response = requests.get(f"{self.host}/v1/models", timeout=5)
            return response.ok
        except requests.RequestException:
            return False
