from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from app.config import get_settings

settings = get_settings()

# Engine único para todo el proyecto
engine = create_engine(
    settings.database_url,
    echo=False,  # cambia a True para debug SQL
    pool_size=5,
    max_overflow=10,
)

# Factory de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency de FastAPI para inyectar sesión en endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def db_session():
    """Context manager para usar fuera de FastAPI (ej: scheduler, scripts)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
