"""
Selección de ofertas para el correo, con Postgres real (testcontainers).
Documenta con tests las decisiones tomadas en app/correo/seleccion.py.
"""

from datetime import datetime, timedelta, timezone

from app.correo.seleccion import marcar_como_enviadas, seleccionar_para_correo
from app.db.models import Correo


def test_ordena_por_score_descendente_y_respeta_limite(db_session, oferta_factory):
    oferta_factory(estado="nueva", score=30)
    oferta_factory(estado="nueva", score=90)
    oferta_factory(estado="nueva", score=60)

    resultado = seleccionar_para_correo(db_session, limite=2, score_minimo=None)

    assert [o.score for o in resultado] == [90, 60]


def test_excluye_ofertas_aplicadas_y_rechazadas(db_session, oferta_factory):
    no_aplicada = oferta_factory(estado="nueva", score=80)
    vista = oferta_factory(estado="vista", score=80)
    aplicada = oferta_factory(estado="aplicada", score=95)
    rechazada = oferta_factory(estado="rechazada", score=95)

    resultado = seleccionar_para_correo(db_session, score_minimo=None)
    ids = {o.id for o in resultado}

    assert no_aplicada.id in ids
    assert vista.id in ids  # 'vista' cuenta como no aplicada -- ver seleccion.py
    assert aplicada.id not in ids
    assert rechazada.id not in ids


def test_excluye_ofertas_sin_score(db_session, oferta_factory):
    con_score = oferta_factory(estado="nueva", score=50)
    sin_score = oferta_factory(estado="nueva", score=None)

    resultado = seleccionar_para_correo(db_session, score_minimo=None)
    ids = {o.id for o in resultado}

    assert con_score.id in ids
    assert sin_score.id not in ids


def test_respeta_score_minimo(db_session, oferta_factory):
    bajo = oferta_factory(estado="nueva", score=20)
    alto = oferta_factory(estado="nueva", score=60)

    resultado = seleccionar_para_correo(db_session, score_minimo=40)
    ids = {o.id for o in resultado}

    assert alto.id in ids
    assert bajo.id not in ids


def test_no_repite_lo_enviado_recientemente(db_session, oferta_factory):
    oferta = oferta_factory(estado="nueva", score=90)
    correo = Correo(oferta_ids=[oferta.id], enviado_en=datetime.now(timezone.utc))
    db_session.add(correo)
    db_session.commit()

    resultado = seleccionar_para_correo(db_session, score_minimo=None)

    assert oferta.id not in {o.id for o in resultado}


def test_reaparece_despues_de_la_ventana_de_exclusion(db_session, oferta_factory):
    """Opción B (design.md): una oferta enviada hace más de
    HORAS_EXCLUSION_REENVIO vuelve a considerarse -- no se pierde para
    siempre, se recuerda si sigue sin aplicarse."""
    oferta = oferta_factory(estado="nueva", score=90)
    hace_dos_dias = datetime.now(timezone.utc) - timedelta(days=2)
    correo = Correo(oferta_ids=[oferta.id], enviado_en=hace_dos_dias)
    db_session.add(correo)
    db_session.commit()

    resultado = seleccionar_para_correo(db_session, score_minimo=None)

    assert oferta.id in {o.id for o in resultado}


def test_sin_ofertas_elegibles_devuelve_lista_vacia(db_session):
    assert seleccionar_para_correo(db_session) == []


def test_marcar_como_enviadas_crea_fila_correos(db_session, oferta_factory):
    o1 = oferta_factory(estado="nueva", score=80)
    o2 = oferta_factory(estado="nueva", score=70)

    correo = marcar_como_enviadas(db_session, [o1, o2])

    assert correo.id is not None
    assert set(correo.oferta_ids) == {o1.id, o2.id}
