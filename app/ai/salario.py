"""
Estimación de salario cuando la oferta no lo publica (requirements.md §4.4).

Decisión tomada al implementar (opción 1 del docstring original): se deriva
de datos que YA tenemos -- promedia ofertas similares ya guardadas en
`ofertas` con salario REAL (no estimado). Gratis, offline, auditable, y no
depende del LLM (evita el riesgo de alucinación de pedirle un número al
modelo). Por eso esta función recibe `db: Session` -- no estaba en la firma
original del esqueleto, pero es necesaria para consultar las referencias.

Si no hay suficientes ofertas similares, devuelve (None, None, None) -- un
salario inventado contamina el score y el dashboard, es peor que un vacío.
"""

import re
from statistics import mean
from typing import Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.connectors.canonical import OfertaCanonica
from app.db.models import Oferta

# Con menos de esto, no hay confianza suficiente en el promedio -> None
MIN_REFERENCIAS = 3

# Palabras que no sirven para matchear "mismo rol" (conectores + niveles,
# el nivel no cuenta como parte del rol para esta comparación)
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "of", "in", "at", "with", "to",
    "de", "la", "el", "y", "en", "para", "con",
    "i", "ii", "iii", "senior", "junior", "sr", "jr",
}


def _palabras_clave(titulo: str) -> set[str]:
    palabras = re.findall(r"[a-záéíóúñ]+", titulo.lower())
    return {p for p in palabras if p not in _STOPWORDS and len(p) > 2}


def estimar_salario(
    db: Session, oferta: OfertaCanonica
) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Promedia el salario de ofertas ya guardadas que: tienen salario REAL
    (salario_estimado=False), comparten país (o modalidad remota si no hay
    país) y al menos una palabra clave del título.

    Returns:
        (salario_min, salario_max, moneda) o (None, None, None).
    """
    palabras_oferta = _palabras_clave(oferta.titulo)
    if not palabras_oferta:
        return None, None, None

    query = db.query(Oferta).filter(
        Oferta.salario_estimado.is_(False),
        or_(Oferta.salario_min.isnot(None), Oferta.salario_max.isnot(None)),
    )
    if oferta.pais:
        query = query.filter(Oferta.pais == oferta.pais)
    elif oferta.modalidad and oferta.modalidad.value == "remoto":
        query = query.filter(Oferta.modalidad == "remoto")

    # Tope defensivo: no queremos escanear toda la tabla sin límite a medida
    # que crece el histórico.
    candidatas = query.limit(200).all()

    referencias = [c for c in candidatas if _palabras_clave(c.titulo) & palabras_oferta]

    if len(referencias) < MIN_REFERENCIAS:
        return None, None, None

    mins = [float(r.salario_min) for r in referencias if r.salario_min is not None]
    maxs = [float(r.salario_max) for r in referencias if r.salario_max is not None]
    monedas = [r.salario_moneda for r in referencias if r.salario_moneda]

    salario_min = round(mean(mins), 2) if mins else None
    salario_max = round(mean(maxs), 2) if maxs else None
    moneda = max(set(monedas), key=monedas.count) if monedas else None

    return salario_min, salario_max, moneda
