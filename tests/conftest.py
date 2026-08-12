"""
TODO (Fase 1): fixtures compartidas de pytest.

Qué implementar acá (ver docs/design.md §4-A):
- `db_session`: fixture que levanta Postgres real vía testcontainers,
  aplica `BreteAI-Infra/db/init/001_schema.sql` y devuelve una sesión
  limpia por test (rollback o schema fresco entre tests).
- `corrida_factory` / `oferta_raw_factory`: helpers para insertar filas de
  prueba sin repetir el mismo INSERT en cada archivo de test (DRY).

DRY: cualquier fixture usada por más de un archivo de test vive acá, no se
copia entre `tests/unit/`, `tests/integration/`, `tests/contract/`.
"""
