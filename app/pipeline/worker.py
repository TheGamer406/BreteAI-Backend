"""
TODO (Fase 2): el worker que consume la cola. Es la ETAPA 2 del pipeline de
`docs/design.md` §1 (`ofertas_raw` pendiente → IA → `ofertas`).

Qué implementar acá:
- `procesar_pendientes(db: Session, limite: int | None = None) -> dict`:
    1. Query a `ofertas_raw` con `estado_proc='pendiente'`
       (usa el índice parcial `idx_raw_cola` que ya existe en la DB).
    2. Para cada fila:
       a. **Re-mapear el payload crudo a `OfertaCanonica`.** Ojo: `payload`
          guarda el JSON ORIGINAL de la fuente (design.md §1), NO el canónico
          → hay que pasarlo por el `_map()` del conector correspondiente.
          Para eso hace falta un registro `fuente -> clase de conector`
          (hoy `pipeline/runner.py` tiene la lista `CONECTORES_REGISTRADOS`;
          conviene extraer un dict `REGISTRO_CONECTORES` compartido en vez de
          duplicar la lista acá — DRY).
       b. `ai/analyzer.analizar_oferta(...)` → `AnalisisIA` validado.
       c. Si falta salario → `ai/salario.estimar_salario(...)` (marca
          `salario_estimado=True`).
       d. Insertar/actualizar la fila en `ofertas` (canónico + campos de IA),
          con `raw_id` apuntando a la raw de origen.
       e. Marcar la raw como `procesada`.
    3. Si algo falla en una fila: marcar esa raw como `error` con `error_msg`
       e `intentos += 1`, y **seguir con las demás** (mismo criterio de
       aislamiento que los conectores en Fase 1). Nunca perder el raw.
    4. Devolver `{"procesadas": int, "errores": int}`.
- `reprocesar_errores(db, max_intentos: int = 3)`: vuelve a encolar las raw
  en `error` que no superaron el tope de intentos (esto es lo que hace que
  el staging valga la pena — se reprocesa sin volver a llamar a las APIs).

Reglas:
- **Commit por oferta, no por lote completo:** si el proceso se cae a la
  mitad de 400 ofertas, lo ya analizado (que costó minutos de GPU) no se
  pierde.
- Idempotencia: `ofertas` también tiene `UNIQUE(fuente, id_externo)` — si la
  oferta ya fue procesada antes, no duplicar (decidir al implementar si se
  re-analiza y actualiza, o se salta; anotarlo en el código).
- Este worker NO se llama desde los conectores. Lo dispara el scheduler
  después de que termina la corrida de scraping (ver `scheduler/jobs.py`:
  hay que agregarle el paso 2 del pipeline).

Dedup semántico: cuando esté `ai/embeddings.py`, acá es donde se llama para
setear `ofertas.similar_a`. Se puede dejar para el final de la fase, no
bloquea que el resto funcione.
"""
