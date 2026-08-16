"""
TODO (Fase 2): worker completo con Postgres real (testcontainers) y Ollama
MOCKEADO. Sin GPU — este test tiene que correr en CI.

Reusar las fixtures que ya existen en `tests/conftest.py`: `db_session`,
`corrida_factory`. Si hace falta sembrar filas en `ofertas_raw`, agregar un
`oferta_raw_factory` ahí (no armar el INSERT a mano en cada test — DRY).

Casos a cubrir:
- **Camino feliz:** raw `pendiente` + mock de Ollama devolviendo JSON válido
  → se crea la fila en `ofertas` con los campos canónicos (del raw) MÁS los
  de IA (score, resumen...), y la raw queda `procesada`.
- **Los campos canónicos vienen del raw, no del LLM:** si el mock devuelve un
  `titulo` distinto al de la fuente, la fila en `ofertas` conserva el de la
  fuente. (Blinda la regla de `ai/schemas.py`.)
- **Salida inválida del LLM:** mock devolviendo basura → la raw queda en
  `error` con `error_msg` e `intentos=1`, y **no** se crea fila en `ofertas`.
- **Aislamiento:** 3 raws pendientes, la del medio hace fallar al LLM → las
  otras 2 se procesan igual (mismo criterio que los conectores en Fase 1).
- **Reproceso:** una raw en `error` con intentos < tope vuelve a la cola con
  `reprocesar_errores()` y, con el mock ya devolviendo JSON válido, termina
  `procesada`.
- **Idempotencia:** correr el worker dos veces sobre la misma raw no duplica
  filas en `ofertas`.

Mockear `app.ai.client.OllamaClient` (o el punto de entrada que se elija en
`analyzer.py`) con `unittest.mock.patch`, igual que se mockea `_fetch()` en
`tests/integration/test_staging_pipeline.py` — mirar ese archivo como
referencia del patrón antes de escribir.
"""
