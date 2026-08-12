"""
Main application entrypoint for BreteAI.
This is where we initialize and run the FastAPI application with the scheduler.
"""

from fastapi import FastAPI
from app.scheduler.jobs import iniciar_scheduler, detener_scheduler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="BreteAI Backend",
    description="Backend para el sistema de búsqueda automatizada de empleo",
    version="0.1.0"
)

# Global variable to store scheduler instance
scheduler = None

@app.on_event("startup")
async def startup_event():
    """Initialize the scheduler when the app starts."""
    global scheduler
    try:
        scheduler = iniciar_scheduler()
        logger.info("Aplicación iniciada con scheduler activo")
    except Exception as e:
        logger.error(f"Error al iniciar el scheduler: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler when the app shuts down."""
    global scheduler
    if scheduler:
        try:
            detener_scheduler(scheduler)
            logger.info("Aplicación detenida, scheduler detenido")
        except Exception as e:
            logger.error(f"Error al detener el scheduler: {str(e)}")

@app.get("/")
async def root():
    return {"message": "BreteAI Backend - Sistema de búsqueda automatizada de empleo"}

if __name__ == "__main__":
    import uvicorn
    from app.config import get_settings

    settings = get_settings()
    # Host/puerto vienen de config (default 127.0.0.1 para dev local;
    # en Docker el compose setea API_HOST=0.0.0.0).
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)