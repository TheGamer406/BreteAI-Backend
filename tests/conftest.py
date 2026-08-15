"""
Fixtures compartidas de pytest (ver docs/design.md §4-A).

`db_session` levanta un Postgres real y efímero vía testcontainers (requiere
Docker corriendo), le aplica el mismo DDL que usa BreteAI-Infra en producción
(BreteAI-Infra/db/init/001_schema.sql) y da una sesión limpia por test.

Se usa scope="session" para el contenedor (levantarlo una vez por corrida de
tests, no por test — es lento) y limpieza de tablas por test para que no se
contaminen entre sí.
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

SCHEMA_SQL_PATH = Path(__file__).parent.parent.parent / "BreteAI-Infra" / "db" / "init" / "001_schema.sql"


@pytest.fixture(scope="session")
def postgres_container():
    from testcontainers.community.postgres import PostgresContainer

    # driver="psycopg": el proyecto usa psycopg v3 (ver requirements.txt),
    # no psycopg2 (default de testcontainers) -- deben coincidir con lo que
    # corre en producción para que el test valide algo representativo.
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as container:
        yield container


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    engine = create_engine(postgres_container.get_connection_url())

    if not SCHEMA_SQL_PATH.exists():
        pytest.skip(f"No se encontró el DDL en {SCHEMA_SQL_PATH} (¿está el submódulo BreteAI-Infra?)")

    schema_sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(schema_sql))

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Sesión limpia por test: trunca todas las tablas de Base antes de cada uno."""
    Session = sessionmaker(bind=db_engine)
    session = Session()

    # Trunca en orden inverso a las dependencias de FK para no chocar con constraints.
    with db_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def corrida_factory(db_session):
    """Helper para crear una Corrida de prueba sin repetir el mismo INSERT
    en cada archivo de test (DRY)."""
    from app.db.models import Corrida

    def _crear(**overrides):
        defaults = {"estado": "enCurso", "fuentes_ok": [], "fuentes_error": []}
        defaults.update(overrides)
        corrida = Corrida(**defaults)
        db_session.add(corrida)
        db_session.commit()
        db_session.refresh(corrida)
        return corrida

    return _crear
