"""
TODO (Fase 3): selección de ofertas para el correo, con Postgres real
(testcontainers). Necesita DB porque son queries -- por eso está en
`integration/` y no en `unit/`.

Reusar las fixtures de `tests/conftest.py` (`db_session`, `oferta_raw_factory`).
Si hace falta sembrar `Oferta` (no solo `OfertaRaw`), agregar un
`oferta_factory` ahí -- no armar el INSERT a mano en cada test (DRY).

Casos a cubrir:
- Ordena por `score` descendente y respeta `limite`.
- **Excluye aplicadas**: sembrar ofertas en varios estados
  (`nueva|vista|aplicada|enProceso|enEspera|respondida|rechazada`) y verificar
  cuáles entran, según la decisión tomada en `seleccion.py`. Este test es la
  documentación ejecutable de esa decisión.
- Excluye ofertas con `score` nulo (la IA no las pudo analizar).
- Respeta `score_minimo` si se implementó.
- **No repite lo ya enviado**: sembrar una fila en `correos` con ciertos
  `oferta_ids` y verificar que esas no vuelven a salir (según la opción A/B/C
  que se haya elegido en `seleccion.py`).
- Sin ofertas elegibles -> devuelve lista vacía (no lanza excepción; `envio.py`
  usa eso para no mandar correo).
- `marcar_como_enviadas()` crea la fila en `correos` con los ids correctos.
"""
