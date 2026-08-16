"""
Cliente SMTP. Única puerta de salida hacia el servidor de correo -- ningún
otro módulo abre conexiones SMTP (DRY, mismo criterio que app/ai/client.py
con el LLM).
"""

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.common.retry import reintentar_con_backoff
from app.config import get_settings

logger = logging.getLogger(__name__)


class ClienteSMTP:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        usuario: Optional[str] = None,
        password: Optional[str] = None,
        remitente: Optional[str] = None,
        usa_tls: Optional[bool] = None,
    ):
        settings = get_settings()
        self.host = host or settings.smtp_host
        self.port = port or settings.smtp_port
        self.usuario = usuario if usuario is not None else settings.smtp_user
        self.password = password if password is not None else settings.smtp_password
        self.remitente = remitente or settings.mail_from or self.usuario
        self.usa_tls = settings.smtp_usa_tls if usa_tls is None else usa_tls

    def enviar(
        self, destinatario: str, asunto: str, html: str, texto_plano: Optional[str] = None
    ) -> None:
        def _intento() -> None:
            self._enviar_una_vez(destinatario, asunto, html, texto_plano)

        reintentar_con_backoff(_intento, etiqueta="[correo.cliente]", logger=logger)

    def _enviar_una_vez(
        self, destinatario: str, asunto: str, html: str, texto_plano: Optional[str]
    ) -> None:
        mensaje = EmailMessage()
        mensaje["Subject"] = asunto
        mensaje["From"] = self.remitente
        mensaje["To"] = destinatario
        mensaje.set_content(texto_plano or "Este correo requiere un cliente compatible con HTML.")
        mensaje.add_alternative(html, subtype="html")

        with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
            if self.usa_tls:
                smtp.starttls()
            if self.usuario and self.password:
                smtp.login(self.usuario, self.password)
            smtp.send_message(mensaje)

    def esta_disponible(self) -> bool:
        """Ping liviano para el healthcheck del smoke test de CI. No manda
        nada, no usa reintentos -- un healthcheck debe fallar rápido."""
        try:
            with smtplib.SMTP(self.host, self.port, timeout=5) as smtp:
                if self.usa_tls:
                    smtp.starttls()
            return True
        except (smtplib.SMTPException, OSError):
            return False
