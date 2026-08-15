"""
Tests de contrato: pegan a las APIs REALES (sin mock). Implementan la
"alerta si un conector se rompe" de docs/requirements.md §4.5 -- si un test
de acá falla, la fuente cambió su formato.

Marcados @pytest.mark.contract -- excluidos de la corrida normal
(`pytest -m "not contract"` en CI); correr aparte con `pytest -m contract`
en un workflow scheduled (ver docs/design.md §4, Transversal).

Adzuna, Greenhouse, Lever y Ashby necesitan credenciales/board configurados
en .env para traer resultados reales -- sin eso, `_fetch()` devuelve lista
vacía por diseño (ver cada conector), así que el assert es "no crashea",
no "trae items".
"""

import pytest

from app.connectors.adzuna import AdzunaConnector
from app.connectors.arbeitnow import ArbeitnowConnector
from app.connectors.ashby import AshbyConnector
from app.connectors.canonical import OfertaCanonica
from app.connectors.greenhouse import GreenhouseConnector
from app.connectors.himalayas import HimalayasConnector
from app.connectors.jobicy import JobicyConnector
from app.connectors.lever import LeverConnector
from app.connectors.remoteok import RemoteOKConnector
from app.connectors.remotive import RemotiveConnector

pytestmark = pytest.mark.contract

# Fuentes que no requieren credenciales/board configurado -- siempre deben
# traer al menos un item real.
CONECTORES_SIN_CREDENCIALES = [
    RemotiveConnector(),
    RemoteOKConnector(),
    ArbeitnowConnector(),
    JobicyConnector(),
    HimalayasConnector(),
]

# Fuentes que requieren config en .env -- si no está, deben devolver vacío
# sin crashear (no es un fallo de contrato, es falta de config local).
CONECTORES_CON_CREDENCIALES = [
    AdzunaConnector(),
    GreenhouseConnector(),
    LeverConnector(),
    AshbyConnector(),
]


@pytest.mark.parametrize(
    "conector", CONECTORES_SIN_CREDENCIALES, ids=lambda c: c.fuente
)
def test_fetch_trae_items_reales(conector):
    """La fuente responde y trae al menos un item -- si esto falla, la API
    cambió de formato/endpoint o está caída."""
    items = conector._fetch()
    assert isinstance(items, list)
    assert len(items) > 0, f"{conector.fuente} no devolvió ningún item"


@pytest.mark.parametrize(
    "conector", CONECTORES_SIN_CREDENCIALES, ids=lambda c: c.fuente
)
def test_fetch_y_map_producen_ofertas_validas(conector):
    """El pipeline completo _fetch() -> _map() sin mock produce al menos
    una OfertaCanonica válida contra datos reales de HOY."""
    items = conector._fetch()
    ofertas = [conector._map(item) for item in items[:10]]
    ofertas = [o for o in ofertas if o is not None]

    assert ofertas, f"{conector.fuente}: ningún item real se mapeó correctamente"
    for oferta in ofertas:
        assert isinstance(oferta, OfertaCanonica)
        assert oferta.titulo
        assert oferta.url


@pytest.mark.parametrize(
    "conector", CONECTORES_CON_CREDENCIALES, ids=lambda c: c.fuente
)
def test_fetch_no_crashea_sin_credenciales(conector):
    """Sin config en .env, _fetch() debe devolver [] (con warning en logs),
    nunca lanzar una excepción no controlada."""
    items = conector._fetch()
    assert isinstance(items, list)
