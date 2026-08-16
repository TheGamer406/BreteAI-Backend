"""
TODO (Fase 4): schemas Pydantic de request/response. **Este archivo ES el
contrato con el frontend** — lo que salga de acá es lo que `lib/tipos.ts` del
portal tiene que espejar.

Qué implementar acá:
- `OfertaResumen`: lo que se muestra en la TABLA (la vista principal). Chico a
  propósito — la tabla lista decenas de filas, mandar la descripción completa
  de cada una es desperdiciar ancho de banda:
    id, titulo, empresa, modalidad, pais, score, estado, fecha_publicacion,
    salario_min, salario_max, salario_moneda, salario_estimado, tiene_similar
- `OfertaDetalle`: todo lo anterior + descripcion, resumen, requisitos,
  beneficios, seniority, empresa_real, score_razon, url, similar_a,
  etiquetas, comentarios[], adjuntos[], historial[].
- `PaginaOfertas`: `{items: list[OfertaResumen], total: int, pagina: int}`.
  **La paginación va desde el día uno**: hoy hay 58 ofertas pero el diseño
  guarda todo el histórico (`requirements.md` §4.7) — en un año son miles.
- `FiltrosOfertas`: empresa, modalidad, pais, estado, score_min, score_max,
  busqueda (texto libre sobre titulo/empresa), orden.
- `CambioEstado`, `ComentarioCrear`, `LoginRequest`, `LoginResponse`.

## Reglas

- **Nunca exponer `embedding`** (768 floats por oferta: inflaría la respuesta
  sin que el portal lo use) ni el `payload` crudo de `ofertas_raw`.
- `salario_estimado` **siempre viaja** junto al monto. El portal tiene que
  poder distinguir "lo dijo la empresa" de "lo estimamos" (`ai/salario.py`),
  y si el campo no llega, no puede.
- Los enums (estado, modalidad) se declaran acá una vez y el frontend los
  espeja. Si el portal hardcodea sus propios strings, se desincronizan.

Al diseñar los endpoints, invocar la skill **`api-design`** (nombres de
recursos, códigos de estado, forma de la paginación y de los errores). Este
archivo y `routers/` deberían quedar consistentes con esa guía.
"""
