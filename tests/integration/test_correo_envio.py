"""
TODO (Fase 3): envío completo contra **MailHog** (SMTP falso en contenedor)
y Postgres real. `design.md` §4-C. **Gmail real nunca en tests.**

Levantar MailHog con testcontainers (`GenericContainer("mailhog/mailhog")`,
puertos 1025 SMTP / 8025 API HTTP) en una fixture de sesión en `conftest.py`,
al lado de `postgres_container` -- mismo patrón. Alternativa: agregarlo al
`docker-compose.yml` de Infra y que el test asuma que está corriendo; preferir
testcontainers para que el test sea autocontenido como el de Postgres.

Config para el test: `SMTP_HOST` = host del contenedor, `SMTP_PORT` = 1025,
`SMTP_USA_TLS=false` (MailHog no habla TLS). Verificar lo recibido con la API
HTTP de MailHog: `GET http://{host}:8025/api/v2/messages`.

Casos a cubrir:
- **Camino feliz:** ofertas elegibles sembradas -> `enviar_correo_ofertas()` ->
  MailHog recibió 1 mensaje, con el `MAIL_TO` correcto de destinatario, asunto
  no vacío, y el cuerpo con los títulos de las ofertas y los links al portal.
- **Se registra en `correos`:** después del envío hay una fila con los
  `oferta_ids` de lo que se mandó.
- **Sin ofertas elegibles -> no se manda nada:** MailHog no recibe ningún
  mensaje y no se crea fila en `correos`. (Evita el correo vacío 4x/día.)
- **SMTP caído no rompe la corrida ni marca como enviadas:** apuntar a un
  puerto muerto -> `enviar_correo_ofertas()` no propaga la excepción hacia
  arriba (o el scheduler la atrapa, según se implemente), y **NO** queda fila
  en `correos` (si quedara, esas ofertas nunca se volverían a mostrar).
  Mockear `app.common.retry.time.sleep` para no esperar los backoffs reales.
- **No re-envía lo ya enviado:** correr el envío dos veces seguidas -> el
  segundo correo no repite las mismas ofertas (según la decisión de
  `seleccion.py`).
"""
