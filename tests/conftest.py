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


@pytest.fixture
def oferta_raw_factory(db_session, corrida_factory):
    """Helper para sembrar OfertaRaw sin repetir el INSERT en cada test
    (usado por tests/integration/test_ai_worker.py)."""
    from app.db.models import OfertaRaw

    contador = {"n": 0}

    def _crear(fuente: str = "remotive", payload: dict | None = None, **overrides):
        contador["n"] += 1
        defaults = {
            "corrida_id": corrida_factory().id,
            "fuente": fuente,
            "id_externo": str(contador["n"]),
            "payload": payload or {},
            "estado_proc": "pendiente",
        }
        defaults.update(overrides)
        raw = OfertaRaw(**defaults)
        db_session.add(raw)
        db_session.commit()
        db_session.refresh(raw)
        return raw

    return _crear


@pytest.fixture
def oferta_factory(db_session, oferta_raw_factory):
    """Helper para sembrar Oferta (no solo OfertaRaw) sin repetir el INSERT
    en cada test (usado por tests/*/test_correo_*.py)."""
    from app.db.models import Oferta

    contador = {"n": 0}

    def _crear(**overrides):
        contador["n"] += 1
        raw = oferta_raw_factory()
        defaults = {
            "raw_id": raw.id,
            "fuente": raw.fuente,
            "id_externo": raw.id_externo,
            "titulo": f"Oferta de prueba {contador['n']}",
            "descripcion": "Descripción de prueba.",
            "url": f"https://example.com/oferta-{contador['n']}",
            "estado": "nueva",
            "score": 50,
        }
        defaults.update(overrides)
        oferta = Oferta(**defaults)
        db_session.add(oferta)
        db_session.commit()
        db_session.refresh(oferta)
        return oferta

    return _crear


@pytest.fixture(scope="session")
def mailhog_container():
    """SMTP falso en contenedor (design.md §4-C) -- vía testcontainers, no
    en el docker-compose.yml de Infra: MailHog es solo para tests, no debe
    correr en producción."""
    from testcontainers.core.container import DockerContainer

    with DockerContainer("mailhog/mailhog:latest").with_exposed_ports(1025, 8025) as container:
        yield container


@pytest.fixture
def mailhog(mailhog_container):
    """Host/puertos de MailHog + helper para leer los mensajes recibidos vía
    su API HTTP. Limpia los mensajes de tests anteriores antes de cada test."""
    import requests

    host = mailhog_container.get_container_host_ip()
    smtp_port = int(mailhog_container.get_exposed_port(1025))
    http_port = int(mailhog_container.get_exposed_port(8025))
    api_base = f"http://{host}:{http_port}/api/v2"

    # Limpiar TODOS los mensajes es un endpoint de la API v1, no v2 (v2 no
    # tiene "delete all", solo borrado individual por ID) -- confirmado
    # corriendo contra un MailHog real, no documentado a ojo.
    requests.delete(f"http://{host}:{http_port}/api/v1/messages")

    class MailHog:
        def __init__(self):
            self.host = host
            self.smtp_port = smtp_port

        def mensajes(self) -> list:
            return requests.get(f"{api_base}/messages").json()["items"]

    return MailHog()
