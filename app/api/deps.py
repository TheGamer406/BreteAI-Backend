"""
TODO (Fase 4): dependencias compartidas de FastAPI.

Qué implementar acá:
- `usuario_actual(...)`: lee el token (de la cookie `httpOnly`, ver
  `routers/auth.py`), lo valida con `api/seguridad.decodificar_token()` y
  devuelve el identificador. Si no hay token o está vencido → `HTTPException(401)`.
  **Es la única forma de proteger un endpoint**: cada router protegido lo pide
  como dependencia. Si un endpoint nuevo se olvida de pedirla, queda abierto —
  por eso el test de auth debe recorrer TODOS los endpoints, no solo uno
  (ver `tests/integration/test_api_auth.py`).
- Re-exportar `get_db` de `app/db/session.py` — NO crear otra sesión acá (DRY).

Distinguir bien los códigos: 401 = no autenticado (falta o venció el token),
403 = autenticado pero sin permiso. Con un solo usuario casi todo es 401.
"""
