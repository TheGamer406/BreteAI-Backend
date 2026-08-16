"""
TODO (Fase 4): endpoints de autenticación.

Endpoints:
- `POST /api/auth/login` — recibe usuario+password, verifica contra
  `ADMIN_USUARIO`/`ADMIN_PASSWORD_HASH`, y si es válido setea la cookie del JWT.
- `POST /api/auth/logout` — borra la cookie.
- `GET  /api/auth/yo` — devuelve el usuario actual o 401. Lo usa el portal al
  cargar para saber si redirigir al login.

## Decisión: cookie httpOnly, no header Authorization

El token va en una cookie `httpOnly; secure; samesite=lax`, no en un header que
el JS del portal tenga que guardar. Motivo: con `localStorage`, cualquier XSS
se lleva el token; con `httpOnly`, el JS ni siquiera puede leerlo. El costo es
tener que pensar CSRF — que `samesite=lax` cubre para este caso (no hay
formularios cross-site legítimos).
`secure=True` solo cuando la app corre sobre HTTPS: en dev sobre localhost hay
que poder desactivarlo o el navegador descarta la cookie. Config: `COOKIE_SECURE`.

## Reglas de seguridad

- **Mismo mensaje de error** para "usuario no existe" y "password incorrecta"
  ("Credenciales inválidas"). Mensajes distintos le dicen a un atacante qué
  usuario existe.
- **Rate limiting** en el login. Es un endpoint expuesto por Tailscale, con un
  solo usuario y sin límite se puede hacer fuerza bruta tranquilo. Algo simple
  (N intentos por IP por minuto) alcanza; no hace falta una dependencia grande.
- **Nunca loguear** la password ni el token, ni siquiera en DEBUG.
"""
