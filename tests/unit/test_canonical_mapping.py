"""
Un test por conector que valida `_map()` contra su fixture real (ver
tests/fixtures/README.md). Sin red — nunca se llama a `_fetch()` acá.

Parametrizado sobre los 9 conectores para no repetir el mismo test 9 veces
(DRY). Los conectores de tipo ATS (Greenhouse/Lever/Ashby) y Adzuna reciben
un campo extra simulando lo que su `_fetch()` real inyecta (`_board_token`,
`_company_slug`, `_board_name`, `_country`) antes de llamar a `_map()`.
"""

import json
from pathlib import Path

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

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

# fuente -> clave del array dentro del JSON de la fuente (None = array plano)
CLAVE_ARRAY = {
    "remotive": "jobs",
    "remoteok": None,
    "arbeitnow": "data",
    "jobicy": "jobs",
    "himalayas": "jobs",
    "adzuna": "results",
    "greenhouse": "jobs",
    "lever": None,
    "ashby": "jobs",
}

# Conectores registrados con su fuente y, si aplica, la metadata que su
# _fetch() real inyecta en cada raw_item antes de pasarlo a _map().
CASOS = [
    (RemotiveConnector(), "remotive", None),
    (RemoteOKConnector(), "remoteok", None),
    (ArbeitnowConnector(), "arbeitnow", None),
    (JobicyConnector(), "jobicy", None),
    (HimalayasConnector(), "himalayas", None),
    (AdzunaConnector(), "adzuna", {"_country": "gb"}),
    (GreenhouseConnector(), "greenhouse", {"_board_token": "gitlab"}),
    (LeverConnector(), "lever", {"_company_slug": "example"}),
    (AshbyConnector(), "ashby", {"_board_name": "notion"}),
]
IDS = [caso[1] for caso in CASOS]


def _cargar_items(fuente: str, extra_field: dict | None) -> list[dict]:
    raw = json.loads((FIXTURES_DIR / f"{fuente}.json").read_text(encoding="utf-8"))

    clave = CLAVE_ARRAY[fuente]
    items = raw if clave is None else raw[clave]

    if fuente == "remoteok":
        items = items[1:]  # el primer elemento es metadata, igual que en _fetch()

    if extra_field:
        for item in items:
            item.update(extra_field)

    return items


@pytest.mark.parametrize("conector,fuente,extra_field", CASOS, ids=IDS)
def test_map_produce_oferta_canonica_valida(conector, fuente, extra_field):
    """Cada conector debe mapear su fixture real a OfertaCanonica sin
    lanzar excepciones, con los campos obligatorios bien formados."""
    items = _cargar_items(fuente, extra_field)
    assert items, f"fixture de {fuente} está vacío"

    ofertas = [conector._map(item) for item in items]
    ofertas = [o for o in ofertas if o is not None]

    assert ofertas, f"ningún item de {fuente} se mapeó correctamente"

    for oferta in ofertas:
        assert isinstance(oferta, OfertaCanonica)
        assert oferta.fuente == fuente
        assert oferta.id_externo, "id_externo no puede estar vacío"
        assert oferta.url, "url no puede estar vacía"
        assert isinstance(oferta.titulo, str)


@pytest.mark.parametrize("conector,fuente,extra_field", CASOS, ids=IDS)
def test_map_no_crashea_con_item_incompleto(conector, fuente, extra_field):
    """Un item vacío/incompleto no debe colgar el proceso. _map() puede
    lanzar una excepción (BaseConnector.run() la atrapa y descarta el item,
    ver app/connectors/base.py) o retornar None -- ambos son manejables.
    Lo único inaceptable sería un hang o un error no capturable."""
    item = dict(extra_field) if extra_field else {}
    try:
        conector._map(item)
    except Exception:
        pass  # esperado y manejado por BaseConnector.run()
