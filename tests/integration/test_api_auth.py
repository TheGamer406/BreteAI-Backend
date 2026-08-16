"""
TODO (Fase 4): autenticación de la API. `TestClient` de FastAPI + Postgres real
(`design.md` §4-D). **El test más importante de la fase.**

Casos a cubrir:
- Login con credenciales correctas → 200 + cookie de sesión seteada.
- Password incorrecta → 401, **y el mismo mensaje** que con usuario inexistente
  (si difieren, se filtra qué usuario existe).
- Usuario inexistente → 401 con ese mismo mensaje.
- Endpoint protegido sin token → 401.
- Endpoint protegido con token inválido/manipulado → 401.
- Token expirado → 401 (generar uno ya vencido, no esperar 7 días).
- Logout → la cookie se limpia y el token deja de servir.
- La cookie sale con `httpOnly` (si no, un XSS se la lleva).
- **El hash nunca es la password en texto plano**: hashear dos veces la misma
  password da resultados distintos (salt), y `verificar_password` acepta ambos.

## El test que evita el agujero real

**Recorrer TODOS los endpoints registrados y verificar que responden 401 sin
autenticar**, iterando sobre `app.routes` en vez de listarlos a mano. Así, un
endpoint nuevo que se olvide de pedir la dependencia `usuario_actual` hace
fallar el test el día que se agrega — no seis meses después. Es la diferencia
entre un test de auth y un test de auth que sirve.
"""
