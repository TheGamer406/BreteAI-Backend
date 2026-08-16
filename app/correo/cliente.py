"""
TODO (Fase 3): cliente SMTP. Única puerta de salida hacia el servidor de
correo -- ningún otro módulo abre conexiones SMTP (DRY, mismo criterio que
`ai/client.py` con el LLM).

Qué implementar acá:
- `class ClienteSMTP` con:
    - `enviar(self, destinatario: str, asunto: str, html: str, texto_plano: str | None = None) -> None`
    - `esta_disponible(self) -> bool`: conexión de prueba para el smoke test
      de CI (`design.md` §4, Transversal), sin mandar nada.
- Usar `smtplib` + `email.message.EmailMessage` de la stdlib. No hace falta
  una dependencia nueva; si igual se agrega una, justificar por qué.
- Multipart: `text/plain` + `text/html` (ver `plantilla.py`).
- Reintentos con backoff ante error de red: **reusar
  `app.common.retry.reintentar_con_backoff`**, NO reimplementar el bucle
  (ya lo comparten `connectors/base.py` y `ai/client.py`).

Config nueva para `app/config.py` y los dos `.env.example`:
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587                 # 587 = STARTTLS (el habitual de Gmail)
    SMTP_USER=tu-correo@gmail.com
    SMTP_PASSWORD=                # App Password de 16 caracteres, NO la del correo
    MAIL_FROM=tu-correo@gmail.com
    MAIL_TO=...                   # ya existe en config
    PORTAL_BASE_URL=http://localhost:3000
    SMTP_USA_TLS=true             # false para MailHog en tests (no habla TLS)

Sobre Gmail (`requirements.md` §10, DECISIÓN cerrada):
- Requiere **App Password**, no la contraseña normal de la cuenta: hay que
  tener 2FA activo y generarla en la config de la cuenta de Google.
- La App Password es un secreto: `.env` (gitignored) y GitHub Secrets para el
  deploy. **Nunca** en el repo, en un log, ni en un mensaje de error.

**En tests nunca se toca Gmail real** (`design.md` §4-C). Se usa MailHog
(servicio a agregar en el `docker-compose.yml` de Infra): habla SMTP plano en
:1025 y expone una API HTTP en :8025 para revisar lo recibido.
"""
