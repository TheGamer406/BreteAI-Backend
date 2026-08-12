from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.pipeline.runner import ejecutar_corrida
import logging

# Configure logging to see what's happening in the scheduler
logger = logging.getLogger(__name__)

# Define the 4 daily runs in Costa Rica timezone (UTC-6)
CR_TIMEZONE_HOURS = -6

def iniciar_scheduler():
    """Inicia el scheduler con las 4 corridas diarias."""
    # Create a background scheduler
    scheduler = BackgroundScheduler()
    
    # Set up cron triggers for 05:00, 11:00, 16:00, 22:00 in Costa Rica timezone (UTC-6)
    triggers = [
        CronTrigger(hour=5, minute=0, timezone='Etc/GMT+6'),   # 05:00 UTC-6
        CronTrigger(hour=11, minute=0, timezone='Etc/GMT+6'),  # 11:00 UTC-6  
        CronTrigger(hour=16, minute=0, timezone='Etc/GMT+6'),  # 16:00 UTC-6
        CronTrigger(hour=22, minute=0, timezone='Etc/GMT+6')   # 22:00 UTC-6
    ]
    
    for i, trigger in enumerate(triggers):
        scheduler.add_job(
            func=ejecutar_corrida,
            trigger=trigger,
            id=f"corrida_diaria_{i}",
            name=f"Corrida diaria {i+1}"
        )
        
    # Start the scheduler
    scheduler.start()
    
    logger.info("Scheduler iniciado con 4 corridas diarias")
    
    return scheduler

def detener_scheduler(scheduler):
    """Detiene el scheduler."""
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler detenido")

