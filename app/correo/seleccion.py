"""
Elegir QUÉ ofertas van en el correo. `envio.py` es el único que llama a este
módulo -- acá no se arma HTML ni se manda nada, solo se consulta y registra.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Correo, Oferta

# Estados que cuentan como "no aplicada" (requirements.md §6, §10). Se
# incluye 'vista' porque tiene sentido recordarle al usuario una oferta que
# abrió pero no llegó a aplicar; el resto de estados ya implican una
# decisión tomada (aplicada, en proceso, rechazada...) y no deben reaparecer.
ESTADOS_NO_APLICADA = ("nueva", "vista")

# Score mínimo para entrar al correo -- evita mandar "ruido" que entrena al
# usuario a ignorar el correo.
SCORE_MINIMO_DEFAULT = 40

# Decisión (opción B del diseño original): una oferta ya incluida en un
# correo en las últimas N horas no se repite. Con 4 corridas/día esto evita
# el mismo correo 4 veces seguidas, pero una oferta de score alto que sigue
# sin aplicarse vuelve a aparecer al día siguiente como recordatorio -- ni
# "nunca más" (se perdería) ni "siempre" (sería ruido).
HORAS_EXCLUSION_REENVIO = 24


def _ids_recientemente_enviados(db: Session, horas: int) -> set[int]:
    desde = datetime.now(timezone.utc) - timedelta(hours=horas)
    correos_recientes = db.query(Correo).filter(Correo.enviado_en >= desde).all()
    ids: set[int] = set()
    for correo in correos_recientes:
        ids.update(correo.oferta_ids)
    return ids


def seleccionar_para_correo(
    db: Session,
    limite: int = 10,
    score_minimo: Optional[int] = SCORE_MINIMO_DEFAULT,
) -> list[Oferta]:
    """Ofertas no aplicadas, con score, ordenadas por score descendente,
    excluyendo lo enviado en las últimas `HORAS_EXCLUSION_REENVIO` horas."""
    excluidos = _ids_recientemente_enviados(db, HORAS_EXCLUSION_REENVIO)

    query = db.query(Oferta).filter(
        Oferta.estado.in_(ESTADOS_NO_APLICADA),
        Oferta.score.isnot(None),
    )
    if score_minimo is not None:
        query = query.filter(Oferta.score >= score_minimo)
    if excluidos:
        query = query.filter(~Oferta.id.in_(excluidos))

    return query.order_by(Oferta.score.desc()).limit(limite).all()


def marcar_como_enviadas(db: Session, ofertas: list[Oferta]) -> Correo:
    """Registra el envío en `correos`. Llamar SOLO después de que el envío
    SMTP salió bien -- ver envio.py."""
    correo = Correo(oferta_ids=[o.id for o in ofertas])
    db.add(correo)
    db.commit()
    db.refresh(correo)
    return correo
