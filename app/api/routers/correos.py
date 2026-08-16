"""
TODO (Fase 4): endpoints de correos — alimenta la vista "último correo"
(`requirements.md` §8).

Endpoints:
- `GET /api/correos/ultimo` — el último correo enviado: `enviado_en` + las
  ofertas que incluía, resueltas a `OfertaResumen` (no solo los ids crudos que
  guarda `correos.oferta_ids`; el portal necesita mostrarlas).
- `GET /api/correos` — historial paginado de envíos (opcional en v1).

Detalle a tener en cuenta: `correos.oferta_ids` es un `BIGINT[]`, no una FK, así
que **una oferta referenciada podría no existir** si se borró. Resolver con un
`WHERE id = ANY(...)` y no asumir que la cantidad devuelta coincide con la
longitud del array — si no, el portal muestra menos ofertas de las esperadas
sin explicación.

Si no hay ningún correo enviado todavía, devolver 200 con un cuerpo vacío
explícito (`{"correo": null}`), no un 404: "todavía no se mandó ninguno" es un
estado normal del sistema, no un error, y el portal tiene que poder mostrar su
estado vacío sin tratar la respuesta como fallo.
"""
