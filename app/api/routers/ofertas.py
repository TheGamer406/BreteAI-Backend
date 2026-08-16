"""
TODO (Fase 4): endpoints de ofertas — el corazón de la API del portal.
Todos requieren `usuario_actual` (ver `api/deps.py`).

## Endpoints

- `GET /api/ofertas` — lista paginada con filtros (`requirements.md` §8):
  empresa, modalidad, pais, estado, score_min/max, búsqueda de texto, orden,
  pagina, por_pagina. Devuelve `PaginaOfertas` (items chicos, ver `schemas.py`).
  Las vistas del portal ("no aplicadas", "aplicadas") son este mismo endpoint
  con distinto filtro de `estado` — **no hacer un endpoint por vista**, o hay
  que mantener la misma lógica de filtrado en varios lugares.
- `GET   /api/ofertas/{id}` — `OfertaDetalle` (incluye comentarios, adjuntos,
  historial y la oferta `similar_a` si existe).
- `PATCH /api/ofertas/{id}/estado` — cambia el estado. **Debe escribir también
  en `oferta_historial`** (de_estado, a_estado): esa tabla es la que alimenta
  la tasa de respuesta y los tiempos del dashboard (Fase 5). Si el cambio de
  estado no deja rastro, el dashboard nace sin datos.
- `PATCH /api/ofertas/{id}/etiquetas` — reemplaza el array de etiquetas.
- `POST  /api/ofertas/{id}/comentarios` y `DELETE /api/comentarios/{id}`.
- `POST  /api/ofertas/{id}/adjuntos` y `GET /api/adjuntos/{id}` (descarga).
- `POST  /api/ofertas/{id}/feedback` — corrección del usuario a un campo de IA.
  Escribe en `feedback_ia`, que ya consume `app/feedback/criterios.py` para
  ajustar el prompt de la próxima corrida. **Esto cierra el ciclo de Fase 2**:
  hasta ahora la tabla existía pero nada la llenaba.

## Rendimiento

- Filtrar y paginar **en SQL**, nunca trayendo todo a Python. Los índices ya
  existen en el DDL (estado, score DESC, empresa, modalidad).
- La lista NO debe traer `descripcion` ni `embedding` (ver `schemas.py`).

## Adjuntos (`requirements.md` §8)

Los archivos van a un **volumen de Docker**, no a la DB — la tabla `adjuntos`
solo guarda `ruta` (así está el DDL). Al implementar:
- Validar tipo y tamaño máximo.
- **Nunca usar el nombre que manda el cliente como ruta en disco** (path
  traversal: un `../../etc/algo` escribe fuera del volumen). Generar un nombre
  propio (uuid) y guardar el nombre original solo como metadato para mostrar.
- Servir la descarga a través del endpoint autenticado, no exponiendo el
  directorio como estático.
"""
