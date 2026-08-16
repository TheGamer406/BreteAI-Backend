"""
Armado del prompt de análisis. Sin red, sin GPU -- son strings puros.

Usa un `Perfil` construido a mano, NUNCA `resources/perfil.toon` (datos
personales reales; los tests no deben depender de él ni exponerlo).
"""

from app.ai.prompts import MAX_DESCRIPCION_CHARS, construir_prompt_analisis
from app.ai.perfil import (
    Candidato,
    CriteriosMatch,
    Perfil,
    Preferencias,
    SalarioPreferencia,
    SkillsTecnicos,
)
from app.connectors.canonical import Modalidad, OfertaCanonica


def _perfil_prueba() -> Perfil:
    return Perfil(
        candidato=Candidato(
            nombre="Test Testerson",
            email="test@example.com",
            telefono="+506 0000-0000",
            linkedin="Test Testerson",
            ubicacion="San Jose, Costa Rica",
            seniority="Junior",
            resumen="Perfil de prueba para tests, no es una persona real.",
        ),
        intereses_rol=["Backend", "Data Science"],
        skills_tecnicos=SkillsTecnicos(lenguajes=["Python", "SQL"]),
        preferencias=Preferencias(
            modalidades=["remoto"],
            ubicaciones_aceptadas=["Costa Rica", "Remoto internacional"],
            reubicacion_internacional=True,
            salario=SalarioPreferencia(
                moneda="USD", actual=0, minimo_neto=1000, ideal_neto=2000,
                tope_ideal_neto=3000, nota="prueba",
            ),
            keywords=["python", "backend", "junior"],
            excluir=["senior lead requerido"],
        ),
        criterios_match=CriteriosMatch(
            peso_skills="alto", peso_seniority="alto",
            peso_salario="medio", peso_modalidad="medio",
            penalizar=["requisitos senior"],
            bonificar=["menciona junior/trainee"],
        ),
    )


def _oferta_prueba(**overrides) -> OfertaCanonica:
    defaults = dict(
        fuente="remotive", id_externo="1", titulo="Backend Developer",
        empresa="Acme", descripcion="Buscamos backend developer.",
        url="https://x.com", modalidad=Modalidad.remoto,
    )
    defaults.update(overrides)
    return OfertaCanonica(**defaults)


def test_prompt_incluye_datos_clave_del_perfil():
    prompt = construir_prompt_analisis(_oferta_prueba(), _perfil_prueba())

    assert "Junior" in prompt
    assert "Backend" in prompt and "Data Science" in prompt
    assert "python, backend, junior" in prompt.lower()
    assert "requisitos senior" in prompt  # penalizar
    assert "menciona junior/trainee" in prompt  # bonificar


def test_prompt_incluye_datos_de_la_oferta():
    oferta = _oferta_prueba(titulo="Python Backend Engineer", empresa="Beta Corp")
    prompt = construir_prompt_analisis(oferta, _perfil_prueba())

    assert "Python Backend Engineer" in prompt
    assert "Beta Corp" in prompt


def test_descripcion_larga_se_trunca():
    descripcion_larga = "<p>Requisito importante.</p>" + ("x" * 50_000)
    oferta = _oferta_prueba(descripcion=descripcion_larga)
    prompt = construir_prompt_analisis(oferta, _perfil_prueba())

    assert len(prompt) < len(descripcion_larga)
    assert "[...descripción truncada...]" in prompt
    # No debe exceder MAX_DESCRIPCION_CHARS + margen razonable del resto del prompt
    assert prompt.count("x") <= MAX_DESCRIPCION_CHARS


def test_descripcion_html_llega_limpia_sin_tags():
    oferta = _oferta_prueba(
        descripcion="<p>Buscamos <b>backend</b> developer.</p><ul><li>Python</li><li>SQL</li></ul>"
    )
    prompt = construir_prompt_analisis(oferta, _perfil_prueba())

    assert "<p>" not in prompt
    assert "<b>" not in prompt
    assert "<li>" not in prompt
    assert "backend" in prompt
    assert "Python" in prompt


def test_criterios_extra_aparecen_cuando_se_pasan():
    prompt = construir_prompt_analisis(
        _oferta_prueba(), _perfil_prueba(),
        criterios_extra=["Si menciona sponsorship de visa, subir el score"],
    )
    assert "sponsorship de visa" in prompt


def test_funciona_sin_criterios_extra():
    prompt = construir_prompt_analisis(_oferta_prueba(), _perfil_prueba(), criterios_extra=None)
    assert "Ajustes de criterios" not in prompt
    assert prompt  # igual genera un prompt válido


def test_pide_json_y_espanol_explicitamente():
    prompt = construir_prompt_analisis(_oferta_prueba(), _perfil_prueba())

    assert "JSON" in prompt
    assert "ESPAÑOL" in prompt or "español" in prompt
    # Los 7 campos del schema deben estar mencionados en las instrucciones
    for campo in ["resumen", "requisitos", "beneficios", "seniority", "empresa_real", "score", "score_razon"]:
        assert campo in prompt
