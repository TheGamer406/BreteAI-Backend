"""
Render del HTML/texto del correo. Sin red, sin SMTP, sin DB -- son strings
puros. Las `Oferta` se construyen a mano, sin sesión (no se accede a
relaciones acá).
"""

import pytest

from app.correo.plantilla import render_correo, render_texto_plano
from app.db.models import Oferta


def _oferta(**overrides) -> Oferta:
    defaults = dict(
        id=1,
        titulo="Backend Developer",
        empresa="Acme",
        modalidad="remoto",
        score=80,
        score_razon="buen match",
        descripcion="x",
        url="https://x.com",
        salario_min=None,
        salario_max=None,
        salario_moneda=None,
        salario_estimado=False,
        similar_a=None,
    )
    defaults.update(overrides)
    return Oferta(**defaults)


def test_render_correo_incluye_todas_las_ofertas_en_el_orden_recibido():
    ofertas = [_oferta(id=i, titulo=f"Oferta{i}", score=100 - i * 10) for i in range(5)]
    _, html = render_correo(ofertas, "http://portal.test")

    for oferta in ofertas:
        assert oferta.titulo in html
    posiciones = [html.index(f"Oferta{i}") for i in range(5)]
    assert posiciones == sorted(posiciones)


def test_render_correo_incluye_link_al_portal_con_id_correcto():
    oferta = _oferta(id=42)
    _, html = render_correo([oferta], "http://portal.test")
    assert "http://portal.test/ofertas/42" in html


def test_render_correo_incluye_score_razon():
    oferta = _oferta(score_razon="Excelente match técnico")
    _, html = render_correo([oferta], "http://portal.test")
    assert "Excelente match técnico" in html


def test_salario_estimado_se_marca_distinto_del_real():
    real = _oferta(id=1, salario_min=1000, salario_max=2000, salario_moneda="USD", salario_estimado=False)
    estimado = _oferta(id=2, salario_min=1000, salario_max=2000, salario_moneda="USD", salario_estimado=True)

    _, html_real = render_correo([real], "http://portal.test")
    _, html_estimado = render_correo([estimado], "http://portal.test")

    assert "(estimado)" not in html_real
    assert "(estimado)" in html_estimado


def test_salario_ausente_muestra_no_especificado():
    oferta = _oferta(salario_min=None, salario_max=None)
    _, html = render_correo([oferta], "http://portal.test")
    assert "no especificado" in html
    assert "None" not in html


def test_oferta_similar_a_muestra_aviso():
    oferta = _oferta(similar_a=99)
    _, html = render_correo([oferta], "http://portal.test")
    assert "Similar a otra oferta" in html


def test_oferta_sin_similar_a_no_muestra_aviso():
    oferta = _oferta(similar_a=None)
    _, html = render_correo([oferta], "http://portal.test")
    assert "Similar a otra oferta" not in html


def test_asunto_no_vacio_y_da_idea_de_la_cantidad():
    asunto, _ = render_correo([_oferta(id=1), _oferta(id=2)], "http://portal.test")
    assert asunto
    assert "2" in asunto


def test_fuentes_con_problemas_aparecen_al_pie():
    _, html = render_correo([_oferta()], "http://portal.test", fuentes_con_problemas=["greenhouse"])
    assert "greenhouse" in html


def test_sin_fuentes_con_problemas_no_hay_seccion_de_alerta():
    _, html = render_correo([_oferta()], "http://portal.test", fuentes_con_problemas=None)
    assert "vienen fallando" not in html


def test_texto_plano_sin_tags_html():
    texto = render_texto_plano([_oferta()], "http://portal.test")
    assert "<" not in texto
    assert ">" not in texto
    assert "http://portal.test/ofertas/1" in texto


def test_lista_vacia_lanza_valueerror():
    with pytest.raises(ValueError):
        render_correo([], "http://portal.test")
    with pytest.raises(ValueError):
        render_texto_plano([], "http://portal.test")
