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

# Factory de sesiones. expire_on_commit=False: los objetos ORM devueltos
# por funciones que usan `with db_session()` (ej: ejecutar_corrida) siguen
# siendo legibles después de que la sesión se cierra al salir del `with`
# (si no, cualquier atributo sin cachear dispara DetachedInstanceError).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

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
