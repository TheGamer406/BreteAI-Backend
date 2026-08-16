"""
Orquesta el envío. Etapa 3 del pipeline (design.md §1: `ofertas` -> correo
top 5-10). Compone seleccion + plantilla + cliente -- no arma HTML ni hace
queries directas.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.alerts.connector_health import fuentes_con_fallas_recurrentes
from app.config import get_settings
from app.correo.cliente import ClienteSMTP
from app.correo.plantilla import render_correo, render_texto_plano
from app.correo.seleccion import marcar_como_enviadas, seleccionar_para_correo
from app.db.models import Correo

logger = logging.getLogger(__name__)


def enviar_correo_ofertas(
    db: Session,
    limite: int = 10,
    client: Optional[ClienteSMTP] = None,
    destinatario: Optional[str] = None,
    portal_base_url: Optional[str] = None,
) -> Optional[Correo]:
    """
    Selecciona ofertas, renderiza, envía y registra -- en ese orden. El
    registro en `correos` ocurre SOLO después de que el envío SMTP salió
    bien: si se registrara antes y el envío fallara, esas ofertas quedarían
    marcadas como "ya vistas" sin que el usuario las haya visto nunca.

    `destinatario`/`portal_base_url` sobreescriben la config (útil para
    tests y para un futuro reenvío manual desde el portal); por defecto
    salen de `MAIL_TO`/`PORTAL_BASE_URL`.
    """
    settings = get_settings()
    destinatario = destinatario or settings.mail_to
    portal_base_url = portal_base_url or settings.portal_base_url

    ofertas = seleccionar_para_correo(db, limite)
    if not ofertas:
        logger.info("[correo] Sin ofertas elegibles, no se manda correo")
        return None

    if not destinatario:
        logger.warning("[correo] MAIL_TO no configurado, no se puede enviar")
        return None

    fuentes_con_problemas = fuentes_con_fallas_recurrentes(db)
    asunto, html = render_correo(ofertas, portal_base_url, fuentes_con_problemas)
    texto = render_texto_plano(ofertas, portal_base_url)

    client = client or ClienteSMTP()
    try:
        client.enviar(destinatario, asunto, html, texto)
    except Exception as e:
        # No tumbar la corrida por un fallo de SMTP: las ofertas ya están
        # guardadas, el correo es solo la notificación (mismo criterio de
        # aislamiento que los conectores en Fase 1 y el worker en Fase 2).
        logger.error(f"[correo] Envío falló, NO se registra como enviado: {e}")
        return None

    correo = marcar_como_enviadas(db, ofertas)
    logger.info(f"[correo] Enviado a {destinatario} con {len(ofertas)} ofertas (correo #{correo.id})")
    return correo
