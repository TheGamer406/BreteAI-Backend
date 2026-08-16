"""
Dedup semántico con embeddings (requirements.md §4.6 y §5.1).

Detecta la misma vacante publicada en dos fuentes distintas (`id_externo`
diferente en cada una, así que la idempotencia de Fase 1 no lo detecta) por
SIGNIFICADO, no por id.

Decisión tomada al implementar: los vectores se guardan en `ofertas.embedding`
(columna JSONB agregada en BreteAI-Infra/db/init/001_schema.sql) y la
comparación es coseno en Python -- no pgvector. Es simple y alcanza para el
volumen real de este proyecto (miles de ofertas, no millones); si el volumen
crece y esto se vuelve lento, revisar esta decisión.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.ai.client import OllamaClient
from app.connectors.canonical import OfertaCanonica
from app.db.models import Oferta

logger = logging.getLogger(__name__)

UMBRAL_SIMILITUD_DEFAULT = 0.9


def calcular_embedding(oferta: OfertaCanonica, client: Optional[OllamaClient] = None) -> list[float]:
    """Embedding de un texto CORTO y estable -- NO la descripción completa
    (cara de embeber y en su mayoría boilerplate legal que hace parecer
    similar a todo)."""
    client = client or OllamaClient()
    texto = f"{oferta.titulo} en {oferta.empresa or 'empresa no especificada'}"
    return client.embeddings(texto)


def _similitud_coseno(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norma_a = sum(x * x for x in a) ** 0.5
    norma_b = sum(y * y for y in b) ** 0.5
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return dot / (norma_a * norma_b)


def buscar_similar(
    db: Session,
    oferta: OfertaCanonica,
    embedding: list[float],
    umbral: float = UMBRAL_SIMILITUD_DEFAULT,
) -> Optional[int]:
    """Devuelve el `ofertas.id` más parecido por encima del umbral, o None.
    Solo compara contra ofertas de OTRAS fuentes (la misma fuente ya la
    cubre la idempotencia de Fase 1, comparar ahí sería redundante)."""
    candidatas = (
        db.query(Oferta)
        .filter(Oferta.fuente != oferta.fuente, Oferta.embedding.isnot(None))
        .all()
    )

    mejor_id: Optional[int] = None
    mejor_similitud = umbral
    for candidata in candidatas:
        similitud = _similitud_coseno(embedding, candidata.embedding)
        if similitud > mejor_similitud:
            mejor_similitud = similitud
            mejor_id = candidata.id

    return mejor_id
