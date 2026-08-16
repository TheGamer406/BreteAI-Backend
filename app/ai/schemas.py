"""
Schema Pydantic de la SALIDA del LLM + parseo tolerante a los vicios típicos
de un modelo local (Riesgo #1, docs/design.md §5). Único lugar del proyecto
que sabe qué forma tiene la respuesta del modelo — analyzer.py y worker.py
nunca parsean JSON del LLM por su cuenta.
"""

import json
import logging
import re
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class RespuestaIAInvalida(Exception):
    """La respuesta del LLM no se pudo recuperar como AnalisisIA válido,
    ni siquiera tolerando fences/preámbulo/truncamiento. worker.py atrapa
    esto para marcar la raw como `error` y reintentarla después."""


class AnalisisIA(BaseModel):
    """Lo que el LLM debe devolver para UNA oferta. Estos son exactamente
    los campos que la capa de IA llena en `ofertas` (ver app/db/models.py,
    clase Oferta, sección "Campos de IA"). NO incluye campos canónicos
    (titulo, empresa, url...) — esos vienen del raw de Fase 1, nunca del LLM."""

    resumen: str
    requisitos: list[str] = Field(default_factory=list)
    beneficios: list[str] = Field(default_factory=list)
    seniority: Optional[str] = None  # junior | mid | senior | None
    empresa_real: Optional[str] = None  # "info de segunda mano" (requirements.md §5.1)
    score: int = Field(ge=0, le=100)  # fuera de rango -> ValidationError, se rechaza
    score_razon: str


# Fences de markdown: ```json ... ``` o ``` ... ```
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _extraer_json_candidato(texto: str) -> str:
    """Intenta aislar el bloque JSON dentro de texto que puede traer fences
    de markdown y/o preámbulo ("Claro, aquí está el análisis: {...}").
    No valida que sea JSON parseable -- solo recorta el candidato más
    probable. La validación real la hace json.loads() en el llamador."""
    texto = texto.strip()

    fence_match = _FENCE_RE.search(texto)
    if fence_match:
        return fence_match.group(1).strip()

    # Sin fences: buscar el primer '{' y el ÚLTIMO '}' -- cubre el caso de
    # preámbulo antes del JSON. Si el texto viene truncado no habrá '}' de
    # cierre y este slice devuelve algo que json.loads() rechazará más abajo
    # (comportamiento correcto: truncado -> error, no un objeto a medias).
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio != -1 and fin != -1 and fin > inicio:
        return texto[inicio : fin + 1]

    return texto


def parsear_respuesta_llm(texto: str) -> AnalisisIA:
    """Recibe el texto CRUDO del modelo y devuelve un AnalisisIA validado.

    Tolera: fences de markdown, preámbulo antes del JSON. NO tolera (lanza
    RespuestaIAInvalida): JSON truncado, campos obligatorios faltantes,
    score fuera de 0-100, respuesta vacía o sin JSON reconocible.
    """
    if not texto or not texto.strip():
        raise RespuestaIAInvalida("Respuesta vacía del LLM")

    candidato = _extraer_json_candidato(texto)

    try:
        datos = json.loads(candidato)
    except json.JSONDecodeError as e:
        raise RespuestaIAInvalida(
            f"No se pudo parsear JSON de la respuesta (posiblemente truncada): {e}"
        ) from e

    if not isinstance(datos, dict):
        raise RespuestaIAInvalida(f"El JSON no es un objeto, es {type(datos).__name__}")

    try:
        return AnalisisIA.model_validate(datos)
    except ValidationError as e:
        raise RespuestaIAInvalida(f"JSON válido pero no cumple el schema: {e}") from e
