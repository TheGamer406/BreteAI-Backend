"""
TODO (Fase 1): pipeline completo con DB real (testcontainers), sin red.

Qué implementar acá (ver docs/design.md §4-A):
- Conector con `_fetch()` mockeado (devuelve el fixture en vez de pegarle a
  la API real) corriendo contra `db_session` (fixture de conftest.py).
- Assert: filas correctas en `ofertas_raw` tras `run()`.
- Assert de idempotencia: correr el mismo conector 2 veces seguidas sobre la
  misma corrida/fixture → NO debe duplicar filas (`UNIQUE fuente,
  id_externo` respetado a nivel de aplicación, no solo de constraint).
- Caso de fallo: `_fetch()` lanza excepción → la corrida no se cae entera,
  el conector queda marcado en error, los demás siguen.
"""
