import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import db_session
from app.pipeline.runner import ejecutar_corrida
from app.pipeline.worker import procesar_pendientes, reprocesar_errores

logger = logging.getLogger(__name__)


def _corrida_completa():
    """Job que dispara el scheduler: scraping (Fase 1) seguido del análisis
    de IA (Fase 2) sobre todo lo pendiente -- incluyendo raws en error que
    entren dentro del tope de reintentos."""
    ejecutar_corrida()

    with db_session() as db:
        reencoladas = reprocesar_errores(db)
        if reencoladas:
            logger.info(f"[scheduler] {reencoladas} raws en error re-encoladas")
        resultado = procesar_pendientes(db)
        logger.info(f"[scheduler] Análisis IA: {resultado}")


def iniciar_scheduler():
    """Inicia el scheduler con las 4 corridas diarias (scraping + IA)."""
    scheduler = BackgroundScheduler()

    # 05:00, 11:00, 16:00, 22:00 hora Costa Rica (UTC-6)
    triggers = [
        CronTrigger(hour=5, minute=0, timezone='Etc/GMT+6'),
        CronTrigger(hour=11, minute=0, timezone='Etc/GMT+6'),
        CronTrigger(hour=16, minute=0, timezone='Etc/GMT+6'),
        CronTrigger(hour=22, minute=0, timezone='Etc/GMT+6'),
    ]

    for i, trigger in enumerate(triggers):
        scheduler.add_job(
            func=_corrida_completa,
            trigger=trigger,
            id=f"corrida_diaria_{i}",
            name=f"Corrida diaria {i + 1}",
        )

    scheduler.start()
    logger.info("Scheduler iniciado con 4 corridas diarias (scraping + IA)")

    return scheduler


def detener_scheduler(scheduler):
    """Detiene el scheduler."""
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler detenido")
