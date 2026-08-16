"""
Golden set: detecta regresiones grandes de score contra el LLM REAL
(docs/design.md §4-B). Corre SOLO en el server/dev con GPU:

    pytest -m golden

Usa el perfil REAL (`cargar_perfil()`, `resources/perfil.toon`) a propósito
-- a diferencia de los tests unitarios/integración, este valida el
comportamiento real de ESTA instalación contra ESTE perfil, no busca ser
portable entre máquinas.
"""

import json
from pathlib import Path

import pytest

from app.ai.analyzer import analizar_oferta
from app.ai.perfil import cargar_perfil
from app.connectors.canonical import Modalidad, OfertaCanonica

pytestmark = pytest.mark.golden

GOLDEN_SET_PATH = Path(__file__).parent.parent / "fixtures" / "golden_set.json"


def _cargar_casos() -> list[dict]:
    datos = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    return datos["casos"]


def _oferta_desde_json(datos: dict) -> OfertaCanonica:
    datos = dict(datos)
    if datos.get("modalidad"):
        datos["modalidad"] = Modalidad(datos["modalidad"])
    return OfertaCanonica(**datos)


CASOS = _cargar_casos()


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_score_dentro_del_rango_esperado(caso):
    perfil = cargar_perfil()
    oferta = _oferta_desde_json(caso["oferta"])

    analisis = analizar_oferta(oferta, perfil)

    minimo, maximo = caso["rango_esperado"]
    assert minimo <= analisis.score <= maximo, (
        f"'{caso['id']}' ({caso['descripcion']}): score={analisis.score} "
        f"fuera del rango esperado [{minimo}, {maximo}]. razon: {analisis.score_razon}"
    )
