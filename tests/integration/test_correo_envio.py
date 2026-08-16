"""
Envío completo contra MailHog (SMTP falso, testcontainers) y Postgres real.
Gmail real nunca en tests.
"""

from unittest.mock import patch

from app.correo.cliente import ClienteSMTP
from app.correo.envio import enviar_correo_ofertas
from app.db.models import Correo


def _cliente_mailhog(mailhog) -> ClienteSMTP:
    return ClienteSMTP(host=mailhog.host, port=mailhog.smtp_port, usa_tls=False, remitente="bot@breteai.test")


def test_camino_feliz_envia_y_registra(db_session, oferta_factory, mailhog):
    oferta_factory(estado="nueva", score=80, titulo="Backend Dev Real")

    resultado = enviar_correo_ofertas(
        db_session,
        client=_cliente_mailhog(mailhog),
        destinatario="usuario@test.com",
        portal_base_url="http://portal.test",
    )

    assert resultado is not None
    mensajes = mailhog.mensajes()
    assert len(mensajes) == 1

    contenido = str(mensajes[0])
    assert "usuario@test.com" in contenido
    assert "Backend Dev Real" in contenido

    assert db_session.query(Correo).count() == 1


def test_sin_ofertas_elegibles_no_envia_nada(db_session, mailhog):
    resultado = enviar_correo_ofertas(
        db_session,
        client=_cliente_mailhog(mailhog),
        destinatario="usuario@test.com",
        portal_base_url="http://portal.test",
    )

    assert resultado is None
    assert mailhog.mensajes() == []
    assert db_session.query(Correo).count() == 0


def test_smtp_caido_no_registra_como_enviado(db_session, oferta_factory):
    oferta_factory(estado="nueva", score=80)
    cliente_roto = ClienteSMTP(host="localhost", port=1, usa_tls=False)  # puerto muerto

    with patch("app.common.retry.time.sleep"):  # no esperar backoffs reales
        resultado = enviar_correo_ofertas(
            db_session,
            client=cliente_roto,
            destinatario="usuario@test.com",
            portal_base_url="http://portal.test",
        )

    assert resultado is None
    assert db_session.query(Correo).count() == 0


def test_no_reenvia_lo_ya_enviado_en_la_misma_corrida(db_session, oferta_factory, mailhog):
    oferta_factory(estado="nueva", score=80, titulo="Unica Oferta")
    cliente = _cliente_mailhog(mailhog)

    r1 = enviar_correo_ofertas(
        db_session, client=cliente, destinatario="usuario@test.com", portal_base_url="http://portal.test"
    )
    assert r1 is not None

    r2 = enviar_correo_ofertas(
        db_session, client=cliente, destinatario="usuario@test.com", portal_base_url="http://portal.test"
    )

    assert r2 is None  # no quedan ofertas elegibles (ya se envió hace <24h)
    assert len(mailhog.mensajes()) == 1  # sigue habiendo un solo correo
