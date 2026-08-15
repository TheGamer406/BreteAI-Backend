"""
Pipeline completo con DB real (testcontainers), sin red — cada conector se
usa con `_fetch()` mockeado para no depender de las APIs externas acá (eso
es responsabilidad de tests/contract/, ver docs/design.md §4-A).
"""

from unittest.mock import patch

from app.connectors.remotive import RemotiveConnector
from app.db.models import OfertaRaw


FIXTURE_REMOTIVE = [
    {
        "id": 111,
        "title": "Backend Engineer",
        "company_name": "Acme",
        "candidate_required_location": "Worldwide",
        "url": "https://remotive.com/jobs/111",
        "description": "desc",
        "publication_date": "2026-08-01T00:00:00",
    },
    {
        "id": 222,
        "title": "Data Analyst",
        "company_name": "Beta",
        "candidate_required_location": "USA",
        "url": "https://remotive.com/jobs/222",
        "description": "desc",
        "publication_date": "2026-08-02T00:00:00",
    },
]


def test_run_guarda_filas_correctas_en_ofertas_raw(db_session, corrida_factory):
    corrida = corrida_factory()
    conector = RemotiveConnector()

    with patch.object(conector, "_fetch", return_value=FIXTURE_REMOTIVE):
        resultado = conector.run(db_session, corrida.id)
        db_session.commit()

    assert resultado == {"ok": 2, "descartados": 0}

    filas = db_session.query(OfertaRaw).filter(OfertaRaw.fuente == "remotive").all()
    assert len(filas) == 2
    ids_externos = {f.id_externo for f in filas}
    assert ids_externos == {"111", "222"}
    # El payload guardado es el raw_item ORIGINAL, no el canónico
    assert filas[0].payload["title"] in ("Backend Engineer", "Data Analyst")
    assert filas[0].estado_proc == "pendiente"


def test_run_dos_veces_no_duplica_idempotencia(db_session, corrida_factory):
    """Correr el mismo conector 2 veces (2 corridas distintas) sobre el
    mismo fixture NO debe duplicar filas -- UNIQUE(fuente, id_externo)."""
    conector = RemotiveConnector()

    corrida1 = corrida_factory()
    with patch.object(conector, "_fetch", return_value=FIXTURE_REMOTIVE):
        conector.run(db_session, corrida1.id)
        db_session.commit()

    corrida2 = corrida_factory()
    with patch.object(conector, "_fetch", return_value=FIXTURE_REMOTIVE):
        resultado2 = conector.run(db_session, corrida2.id)
        db_session.commit()

    # La segunda corrida "guarda" (ok=2) porque guardar_raw() no distingue
    # entre insertar y detectar-existente en su valor de retorno -- lo que
    # importa es que NO se duplicó en la tabla:
    assert resultado2["ok"] == 2
    total_filas = db_session.query(OfertaRaw).filter(OfertaRaw.fuente == "remotive").count()
    assert total_filas == 2, "la segunda corrida no debe duplicar filas ya existentes"


def test_run_conector_que_falla_no_pierde_items_ya_guardados(db_session, corrida_factory):
    """Si _fetch() lanza una excepción tras agotar los reintentos, run()
    debe propagarla (para que runner.py marque el conector en error) sin
    haber guardado ninguna fila a medias."""
    corrida = corrida_factory()
    conector = RemotiveConnector()

    with patch.object(conector, "_fetch", side_effect=ConnectionError("API caída")), \
         patch("app.connectors.base.time.sleep"):  # no esperar los backoffs reales en el test
        try:
            conector.run(db_session, corrida.id)
            assert False, "run() debería haber propagado la excepción"
        except ConnectionError:
            pass

    filas = db_session.query(OfertaRaw).filter(OfertaRaw.fuente == "remotive").count()
    assert filas == 0
