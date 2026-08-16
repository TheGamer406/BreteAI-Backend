"""
TODO (Fase 4): hash de contraseña y emisión/validación de JWT.
**Empezar por acá** — todo lo demás de la API depende de esto, y es donde un
error se paga caro.

Qué implementar acá:
- `hashear_password(plano: str) -> str` y `verificar_password(plano, hash) -> bool`
  usando **argon2 o bcrypt** (`requirements.md` §7, decisión cerrada). Nunca
  texto plano, nunca sha256 pelado (es rápido = es malo para passwords).
- `crear_token(sub: str) -> str` y `decodificar_token(token: str) -> str | None`
  con expiración. Firmar con `JWT_SECRET` de config.

Dependencia nueva a agregar a requirements.txt: `argon2-cffi` (o `bcrypt`) y
`pyjwt`. Pinear versión como el resto del archivo.

Config nueva para `app/config.py` y los dos `.env.example`:
    JWT_SECRET=              # generar con: python -c "import secrets;print(secrets.token_urlsafe(32))"
    JWT_EXPIRA_HORAS=168     # 7 días: es de un solo usuario y uso diario,
                             # pedirle login todos los días es fricción sin ganancia
    ADMIN_USUARIO=jose
    ADMIN_PASSWORD_HASH=     # el hash, NO la contraseña

## Decisión abierta: ¿dónde vive el usuario?

El DDL de Infra **no tiene tabla `usuarios`** (son 8 tablas, ninguna de auth).
Como es single-user (`requirements.md` §7), hay dos caminos:
  a) **Hash en `.env`** (`ADMIN_PASSWORD_HASH`). Cero migración, cero tabla,
     y el secreto vive donde viven los demás secretos. Cambiar la contraseña
     = regenerar el hash y reiniciar.
  b) **Tabla `usuarios`** en el DDL. Permite cambiar la contraseña desde el
     portal y abre la puerta a multiusuario (que hoy está en el backlog).
Arrancar por (a) — es proporcional al requerimiento real. Si algún día entra
multiusuario, ahí se migra. **Dejar la decisión escrita en el código.**

## No hacer

- No inventar roles/permisos: es UN usuario. Un rol es complejidad sin caso de uso.
- No guardar el JWT en `localStorage` desde el frontend (queda expuesto a XSS).
  Ver `lib/api.ts` del frontend: la decisión es cookie `httpOnly`.
"""
