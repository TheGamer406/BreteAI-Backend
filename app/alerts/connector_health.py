"""
Alerta cuando un conector falla (docs/requirements.md §4.5).

Por ahora: log estructurado nivel ERROR. El canal real de notificación al
usuario es correo (Fase 3) — este módulo NO manda correos, solo deja el
registro que Fase 3 va a poder leer para armar la alerta.
"""

import logging

logger = logging.getLogger("breteai.connector_health")


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
    # TODO (Fase 3): si este conector falla en N corridas seguidas, incluirlo
    # en el correo de alerta en vez de solo loguear. Requiere consultar el
    # historial de `corridas.fuentes_error` de las últimas N filas.
