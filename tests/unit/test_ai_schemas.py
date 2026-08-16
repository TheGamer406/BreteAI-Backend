"""
Validación de la salida del LLM contra fixtures REALES (capturadas de
corridas contra qwen2.5-7b-instruct, ver tests/fixtures/ollama/README.md).
Sin red, sin GPU -- el test más importante de Fase 2 (Riesgo #1, design.md §5).
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ai.schemas import AnalisisIA, RespuestaIAInvalida, parsear_respuesta_llm

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "ollama"


def _leer(nombre: str) -> str:
    return (FIXTURES_DIR / nombre).read_text(encoding="utf-8")


def test_json_valido_y_completo():
    resultado = parsear_respuesta_llm(_leer("respuesta_valida.json"))
    assert isinstance(resultado, AnalisisIA)
    assert 0 <= resultado.score <= 100
    assert resultado.resumen


def test_json_envuelto_en_fences_markdown():
    resultado = parsear_respuesta_llm(_leer("respuesta_con_fences.txt"))
    assert resultado.score == 40
    assert resultado.resumen == "prueba de fences"


def test_json_con_preambulo():
    resultado = parsear_respuesta_llm(_leer("respuesta_con_preambulo.txt"))
    assert resultado.score == 60
    assert resultado.resumen == "prueba de preambulo"


def test_json_truncado_rechaza_sin_devolver_objeto_a_medias():
    with pytest.raises(RespuestaIAInvalida):
        parsear_respuesta_llm(_leer("respuesta_truncada.txt"))


def test_score_fuera_de_rango_rechaza():
    """150 no es un score válido -- NO se trunca a 100 ni se asume 0."""
    with pytest.raises(RespuestaIAInvalida):
        parsear_respuesta_llm(_leer("respuesta_score_invalido.json"))


def test_score_negativo_rechaza():
    with pytest.raises(RespuestaIAInvalida):
        parsear_respuesta_llm(
            '{"resumen":"x","requisitos":[],"beneficios":[],"seniority":null,'
            '"empresa_real":null,"score":-10,"score_razon":"x"}'
        )


def test_respuesta_sin_json_rechaza():
    with pytest.raises(RespuestaIAInvalida):
        parsear_respuesta_llm(_leer("respuesta_sin_json.txt"))


def test_respuesta_vacia_rechaza():
    with pytest.raises(RespuestaIAInvalida):
        parsear_respuesta_llm("")


def test_campo_obligatorio_faltante_rechaza():
    """Sin 'score' (obligatorio) debe rechazar, no asumir un default."""
    with pytest.raises(RespuestaIAInvalida):
        parsear_respuesta_llm('{"resumen":"x","score_razon":"x"}')


def test_requisitos_tipo_incorrecto_rechaza():
    """'requisitos' debe ser una lista de strings, no un string suelto."""
    with pytest.raises(RespuestaIAInvalida):
        parsear_respuesta_llm(
            '{"resumen":"x","requisitos":"Python, SQL","beneficios":[],'
            '"seniority":null,"empresa_real":null,"score":50,"score_razon":"x"}'
        )


def test_analisis_ia_valida_score_directamente():
    """El modelo Pydantic en sí también rechaza score fuera de rango,
    independiente del parser (blinda el schema si algo lo instancia directo)."""
    with pytest.raises(ValidationError):
        AnalisisIA(
            resumen="x", seniority=None, empresa_real=None, score=101, score_razon="x"
        )
