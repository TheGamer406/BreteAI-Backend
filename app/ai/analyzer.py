"""
Orquesta el análisis de UNA oferta: prompt -> LLM -> validación. Template
method de la capa de IA, equivalente a `connectors/base.py` en Fase 1.

No toca la DB ni sabe de `ofertas_raw`/estados de procesamiento -- eso es
responsabilidad de `app/pipeline/worker.py` (misma separación que
`connectors/base.py` <-> `app/pipeline/staging.py`).
"""

import logging
import time
from typing import Optional

from app.ai.client import OllamaClient
from app.ai.perfil import Perfil
from app.ai.prompts import construir_prompt_analisis
from app.ai.schemas import AnalisisIA, RespuestaIAInvalida, parsear_respuesta_llm
from app.connectors.canonical import OfertaCanonica

logger = logging.getLogger(__name__)

MAX_REINTENTOS_PARSEO = 2  # el modelo es no determinista, reintentar suele arreglar un JSON roto


def analizar_oferta(
    oferta: OfertaCanonica,
    perfil: Perfil,
    criterios_extra: Optional[list[str]] = None,
    client: Optional[OllamaClient] = None,
) -> AnalisisIA:
    """Analiza una oferta contra el perfil y devuelve un AnalisisIA validado.

    Si la respuesta del LLM no se puede parsear, reintenta hasta
    MAX_REINTENTOS_PARSEO veces (nueva llamada al modelo, no solo re-parsear
    el mismo texto). Tras agotar los reintentos, propaga RespuestaIAInvalida
    para que el worker marque la raw como `error` y la reprocese después.
    """
    client = client or OllamaClient()
    prompt = construir_prompt_analisis(oferta, perfil, criterios_extra)

    ultimo_error: Optional[RespuestaIAInvalida] = None
    for intento in range(1, MAX_REINTENTOS_PARSEO + 1):
        inicio = time.monotonic()
        texto = client.generar(prompt, formato_json=True)
        duracion = time.monotonic() - inicio

        try:
            analisis = parsear_respuesta_llm(texto)
            logger.info(
                f"[analyzer] '{oferta.titulo}' analizada en {duracion:.1f}s "
                f"(intento {intento}), score={analisis.score}"
            )
            return analisis
        except RespuestaIAInvalida as e:
            ultimo_error = e
            logger.warning(
                f"[analyzer] '{oferta.titulo}': respuesta inválida en intento "
                f"{intento}/{MAX_REINTENTOS_PARSEO} ({duracion:.1f}s): {e}"
            )

    assert ultimo_error is not None
    raise ultimo_error
