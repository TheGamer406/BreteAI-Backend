"""
TODO (Fase 2, puede ir al final): dedup semántico con embeddings
(`requirements.md` §4.6 y §5.1).

Problema que resuelve: la misma vacante publicada en Remotive y en RemoteOK
tiene `id_externo` distinto, así que la idempotencia de Fase 1 no la detecta.
Acá se detecta por SIGNIFICADO (mismo puesto + misma empresa, aunque el
título esté redactado distinto).

Qué implementar acá:
- `calcular_embedding(oferta: OfertaCanonica) -> list[float]`: usa
  `client.OllamaClient().embeddings(...)` sobre un texto corto y estable
  (ej: `f"{titulo} en {empresa}"` — NO la descripción completa: es cara de
  embeber y la mitad es boilerplate legal que hace parecer similar a todo).
- `buscar_similar(db, oferta, umbral: float = 0.9) -> int | None`: devuelve el
  `ofertas.id` de la oferta más parecida por encima del umbral, o None.
  El resultado es lo que se guarda en `ofertas.similar_a` (la columna ya
  existe en el DDL).

Decisión pendiente al implementar (anotarla en el código cuando se resuelva):
dónde guardar los vectores. Opciones:
  a) Columna nueva en `ofertas` + comparación en Python (simple; suficiente
     para unos miles de ofertas, que es la escala real de este proyecto).
  b) Extensión `pgvector` en Postgres (más "correcto", pero agrega una
     dependencia de infra a mantener en el server).
Arrancar por (a) salvo que el volumen demuestre que no alcanza. Si se elige
(a), la columna hay que agregarla al DDL de `BreteAI-Infra` **y** al modelo
ORM — no inventarla solo en el ORM.

Marcar "similar a" NO es borrar: el histórico se guarda completo
(`requirements.md` §4.7). El portal muestra el aviso, el usuario decide.
"""
