import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.models import OfertaRaw

logger = logging.getLogger(__name__)

def guardar_raw(
    db: Session,
    corrida_id: int,
    fuente: str,
    id_externo: str,
    payload: Dict[str, Any],
) -> OfertaRaw:
    """
    Guarda una oferta en `ofertas_raw` con idempotencia vía UNIQUE(fuente, id_externo).

    Si ya existe esa combinación (oferta ya vista en una corrida anterior), NO duplicar
    — retorna la fila existente sin cambiarla (conserva el payload original).

    Args:
        db: Sesión SQLAlchemy (requiere que el llamador gestione el commit).
        corrida_id: ID de la corrida actual.
        fuente: Identificador de la fuente ("remotive", "greenhouse", etc.).
        id_externo: ID único de la oferta EN QUELLA fuente.
        payload: Datos completos de la oferta como dict (JSON crudo, sin procesar).

    Returns:
        OfertaRaw: La fila nueva o existente (no se actualiza si ya existe).

    Raises:
        Exception: Si hay error de BD que no sea UNIQUE (ex: FK inválida).
    """
    try:
        # Buscar si ya existe esa combinación (fuente + id_externo)
        existing = db.query(OfertaRaw).filter(
            OfertaRaw.fuente == fuente,
            OfertaRaw.id_externo == id_externo,
        ).first()

        if existing:
            logger.debug(f"Oferta ya existe (idempotencia): {fuente}/{id_externo}")
            return existing

        # Nueva oferta: insertarla
        oferta_raw = OfertaRaw(
            corrida_id=corrida_id,
            fuente=fuente,
            id_externo=id_externo,
            payload=payload,
            estado_proc="pendiente",
        )
        db.add(oferta_raw)
        # db.commit() lo hace el llamador (runner.py) para que pueda hacer rollback de la corrida completa si falla

        return oferta_raw

    except IntegrityError:
        # Si UNIQUE(fuente, id_externo) se viola a pesar del check arriba,
        # significa race condition (otra corrida insertó la misma oferta).
        # En ese caso, rollback local y retornar la que existe.
        db.rollback()
        logger.warning(f"Race condition en {fuente}/{id_externo}, usando existente")
        existing = db.query(OfertaRaw).filter(
            OfertaRaw.fuente == fuente,
            OfertaRaw.id_externo == id_externo,
        ).first()
        return existing

    except Exception as e:
        logger.error(f"Error al guardar en ofertas_raw: {str(e)}")
        raise
