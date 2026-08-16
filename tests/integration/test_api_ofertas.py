"""
TODO (Fase 4): endpoints de ofertas con Postgres real. Reusar las fixtures de
`tests/conftest.py` (`db_session`, `oferta_factory`) — ya existen de Fase 3.
Hará falta una fixture nueva `cliente_autenticado` que devuelva un `TestClient`
con la cookie ya puesta (para no repetir el login en cada test).

Casos a cubrir:
- Listado: paginación (total y página correctos), orden por score descendente.
- Cada filtro por separado: empresa, modalidad, pais, estado, score_min/max,
  búsqueda de texto. Y al menos uno combinado (los filtros se pisan entre sí
  con más facilidad de la que parece).
- La respuesta del listado **no trae `descripcion` ni `embedding`** — si se
  cuelan, la respuesta se infla y nadie se da cuenta hasta producción.
- `salario_estimado` viaja siempre junto al monto.
- Detalle: incluye comentarios, adjuntos e historial; 404 si el id no existe.
- **Cambio de estado escribe en `oferta_historial`** con `de_estado` y
  `a_estado` correctos. Sin esto, el dashboard de Fase 5 nace sin datos.
- Comentarios: crear, listar, borrar.
- Feedback: `POST /feedback` crea la fila en `feedback_ia` y
  `app.feedback.criterios.derivar_criterios()` la devuelve después (cierra el
  ciclo con Fase 2).
- Adjuntos: subir uno chico, descargarlo, y que **un nombre malicioso
  (`../../evil.txt`) no escriba fuera del directorio**.
"""
