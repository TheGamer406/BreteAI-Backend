"""
Alerta cuando un conector falla (docs/requirements.md §4.5).

`registrar_fallo()` deja el log estructurado en cada corrida.
`fuentes_con_fallas_recurrentes()` es el canal real (Fase 3): revisa las
últimas corridas y devuelve las fuentes que vienen fallando en TODAS ellas,
para incluirlas como aviso al pie del correo (app/correo/plantilla.py) --
un fallo puntual de red no genera alerta, uno sostenido sí.
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.db.models import Corrida

logger = logging.getLogger("breteai.connector_health")

# Cuántas corridas seguidas tiene que fallar una fuente para considerarse
# "recurrente" (evita alertar por un error de red puntual).
CORRIDAS_PARA_ALERTA = 3


def registrar_fallo(fuente: str, error: Exception, corrida_id: int) -> None:
    """
    Registra que un conector falló en una corrida.

    No confundir con app.pipeline.staging — acá no se toca `ofertas_raw`,
    solo se deja constancia de que algo salió mal para poder alertar después.
    """
    logger.error(
        f"Conector fallido: fuente={fuente} corrida_id={corrida_id} error={error}",
        extra={"fuente": fuente, "corrida_id": corrida_id},
    )


def fuentes_con_fallas_recurrentes(
    db: Session, corridas_para_alerta: int = CORRIDAS_PARA_ALERTA
) -> List[str]:
    """Fuentes presentes en `fuentes_error` de las últimas `corridas_para_alerta`
    corridas, TODAS ellas -- no solo la última. Si hay menos corridas que ese
    número todavía, no hay suficiente historial para alertar (devuelve [])."""
    ultimas = db.query(Corrida).order_by(Corrida.id.desc()).limit(corridas_para_alerta).all()
    if len(ultimas) < corridas_para_alerta:
        return []

    conjuntos = [set(c.fuentes_error) for c in ultimas]
    interseccion = set.intersection(*conjuntos) if conjuntos else set()
    return sorted(interseccion)
