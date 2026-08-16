"""
Worker completo con Postgres real (testcontainers) y LLM MOCKEADO. Sin GPU
-- corre en CI. Mismo patrón que tests/integration/test_staging_pipeline.py
(mockear el punto de entrada externo, DB real).

`cargar_perfil()` se mockea con un Perfil de prueba en vez de leer
`resources/perfil.toon` -- el test no debe depender de datos privados
locales (mismo criterio que tests/unit/test_prompts.py).
"""

from unittest.mock import patch

from app.ai.client import OllamaClient
from app.ai.perfil import (
    Candidato,
    CriteriosMatch,
    Perfil,
    Preferencias,
    SalarioPreferencia,
    SkillsTecnicos,
)
from app.db.models import Oferta, OfertaRaw
from app.pipeline.worker import procesar_pendientes, reprocesar_errores

JSON_VALIDO = (
    '{"resumen":"ok","requisitos":["Python"],"beneficios":[],'
    '"seniority":"junior","empresa_real":null,"score":80,"score_razon":"buen match"}'
)
EMBEDDING_FALSO = [0.1] * 768


def _perfil_prueba() -> Perfil:
    return Perfil(
        candidato=Candidato(
            nombre="Test", email="t@example.com", telefono="+506 0000-0000",
            linkedin="Test", ubicacion="Costa Rica", seniority="Junior",
            resumen="Perfil de prueba.",
        ),
        skills_tecnicos=SkillsTecnicos(lenguajes=["Python"]),
        preferencias=Preferencias(
            salario=SalarioPreferencia(
                moneda="USD", actual=0, minimo_neto=1000, ideal_neto=2000,
                tope_ideal_neto=3000, nota="prueba",
            ),
        ),
        criterios_match=CriteriosMatch(
            peso_skills="alto", peso_seniority="alto",
            peso_salario="medio", peso_modalidad="medio",
        ),
    )


def _payload_remotive(id_externo: str, titulo: str) -> dict:
    """Payload crudo con la forma real de Remotive (ver tests/fixtures/remotive.json)."""
    return {
        "id": int(id_externo),
        "title": titulo,
        "company_name": "Acme",
        "candidate_required_location": "Worldwide",
        "url": f"https://remotive.com/jobs/{id_externo}",
        "description": "Backend developer position.",
        "publication_date": "2026-08-01T00:00:00",
    }


def _crear_raw(factory, id_externo: str, titulo: str, fuente: str = "remotive"):
    """Wrapper del factory que fuerza `OfertaRaw.id_externo` a coincidir con
    el `id` del payload -- así se comporta `guardar_raw()` en producción
    (ver app/pipeline/staging.py), y evita confundir el id_externo de la
    fila de staging con el id_externo canónico que sale de _map()."""
    return factory(fuente=fuente, id_externo=id_externo, payload=_payload_remotive(id_externo, titulo))


def _mocks():
    """Contexto con cargar_perfil, OllamaClient.generar y .embeddings
    mockeados. generar() devuelve JSON_VALIDO por defecto -- override con
    side_effect en el test que lo necesite."""
    return (
        patch("app.pipeline.worker.cargar_perfil", return_value=_perfil_prueba()),
        patch.object(OllamaClient, "generar", return_value=JSON_VALIDO),
        patch.object(OllamaClient, "embeddings", return_value=EMBEDDING_FALSO),
    )


def test_camino_feliz_crea_oferta_y_marca_raw_procesada(db_session, oferta_raw_factory):
    raw = _crear_raw(oferta_raw_factory, "1", "Backend Dev")

    p1, p2, p3 = _mocks()
    with p1, p2, p3:
        resultado = procesar_pendientes(db_session)

    assert resultado == {"procesadas": 1, "errores": 0}

    oferta = db_session.query(Oferta).filter(Oferta.fuente == "remotive", Oferta.id_externo == "1").first()
    assert oferta is not None
    assert oferta.score == 80
    assert oferta.seniority == "junior"
    assert oferta.resumen == "ok"

    db_session.refresh(raw)
    assert raw.estado_proc == "procesada"


def test_campos_canonicos_vienen_del_raw_no_del_llm(db_session, oferta_raw_factory):
    """AnalisisIA no tiene campo `titulo` -- aunque el LLM devuelva basura
    ahí, se ignora (Pydantic extra=ignore). El título en `ofertas` es
    siempre el de la fuente."""
    _crear_raw(oferta_raw_factory, "2", "Título Real De La Fuente")

    json_con_titulo_falso = (
        '{"titulo":"TITULO INVENTADO POR EL LLM","resumen":"ok","requisitos":[],'
        '"beneficios":[],"seniority":null,"empresa_real":null,"score":50,"score_razon":"ok"}'
    )

    p1, p2, p3 = _mocks()
    with p1, patch.object(OllamaClient, "generar", return_value=json_con_titulo_falso), p3:
        procesar_pendientes(db_session)

    oferta = db_session.query(Oferta).filter(Oferta.id_externo == "2").first()
    assert oferta.titulo == "Título Real De La Fuente"


def test_salida_invalida_del_llm_queda_en_error(db_session, oferta_raw_factory):
    raw = _crear_raw(oferta_raw_factory, "3", "Backend Dev")

    p1, p2, p3 = _mocks()
    with p1, patch.object(OllamaClient, "generar", return_value="esto no es JSON"), p3, \
         patch("app.ai.analyzer.time.sleep"):  # no esperar entre reintentos de parseo en el test
        resultado = procesar_pendientes(db_session)

    assert resultado == {"procesadas": 0, "errores": 1}

    db_session.refresh(raw)
    assert raw.estado_proc == "error"
    assert raw.error_msg
    assert raw.intentos == 1

    assert db_session.query(Oferta).filter(Oferta.id_externo == "3").first() is None


def test_aislamiento_una_raw_falla_las_demas_se_procesan(db_session, oferta_raw_factory):
    _crear_raw(oferta_raw_factory, "10", "Oferta A")
    _crear_raw(oferta_raw_factory, "11", "Oferta FALLA")
    _crear_raw(oferta_raw_factory, "12", "Oferta C")

    def generar_condicional(self, prompt, formato_json=True):
        if "Oferta FALLA" in prompt:
            return "respuesta invalida"
        return JSON_VALIDO

    p1, _, p3 = _mocks()
    with p1, patch.object(OllamaClient, "generar", generar_condicional), p3, \
         patch("app.ai.analyzer.time.sleep"):
        resultado = procesar_pendientes(db_session)

    assert resultado == {"procesadas": 2, "errores": 1}

    ofertas_ids = {o.id_externo for o in db_session.query(Oferta).all()}
    assert ofertas_ids == {"10", "12"}

    raw_fallida = db_session.query(OfertaRaw).filter(OfertaRaw.id_externo == "11").first()
    assert raw_fallida.estado_proc == "error"


def test_reprocesar_errores_reencola_y_procesar_pendientes_lo_completa(db_session, oferta_raw_factory):
    raw = _crear_raw(oferta_raw_factory, "20", "Backend Dev")

    p1, p2, p3 = _mocks()
    with p1, patch.object(OllamaClient, "generar", return_value="basura"), p3, \
         patch("app.ai.analyzer.time.sleep"):
        procesar_pendientes(db_session)

    db_session.refresh(raw)
    assert raw.estado_proc == "error"
    assert raw.intentos == 1

    reencoladas = reprocesar_errores(db_session)
    assert reencoladas == 1

    db_session.refresh(raw)
    assert raw.estado_proc == "pendiente"

    with p1, p2, p3:
        resultado = procesar_pendientes(db_session)

    assert resultado == {"procesadas": 1, "errores": 0}
    db_session.refresh(raw)
    assert raw.estado_proc == "procesada"


def test_reprocesar_la_misma_raw_no_duplica_ofertas(db_session, oferta_raw_factory):
    """Idempotencia real: `ofertas_raw` tiene UNIQUE(fuente, id_externo), así
    que nunca hay dos raws distintas para la misma oferta -- el escenario
    real es la MISMA raw reprocesada dos veces (ej: el worker se cae después
    de crear la Oferta pero antes de marcar la raw como 'procesada', y una
    corrida posterior la vuelve a tomar). No debe duplicar la fila en
    `ofertas`, y la segunda vez no debe volver a llamar al LLM."""
    raw = _crear_raw(oferta_raw_factory, "30", "Backend Dev")

    p1, p2, p3 = _mocks()
    with p1, p2, p3:
        procesar_pendientes(db_session)

    # Simula que la raw quedó "pendiente" otra vez (crash recovery)
    db_session.refresh(raw)
    raw.estado_proc = "pendiente"
    db_session.commit()

    with p1, patch.object(OllamaClient, "generar", return_value=JSON_VALIDO) as generar_mock, p3:
        resultado = procesar_pendientes(db_session)

    assert resultado == {"procesadas": 1, "errores": 0}
    generar_mock.assert_not_called()  # existía -> no se re-analiza, ahorra GPU

    total_ofertas = (
        db_session.query(Oferta)
        .filter(Oferta.fuente == "remotive", Oferta.id_externo == "30")
        .count()
    )
    assert total_ofertas == 1

    db_session.refresh(raw)
    assert raw.estado_proc == "procesada"
