"""
TODO (Fase 1, opcional/posterior): tests de contrato contra las APIs reales.

Marcar TODOS los tests de este archivo con `@pytest.mark.contract` — deben
quedar excluidos de la corrida normal de CI (que corre en cada push) y solo
ejecutarse en un workflow scheduled aparte (ver docs/design.md §4, Transversal).
Este archivo es lo que implementa la "alerta si un conector se rompe" de
docs/requirements.md §4.5: si un test de acá falla, la fuente cambió su
formato.

Patrón por conector: llamar `_fetch()` real (sin mock) → assert que la
respuesta tiene la forma esperada (claves mínimas presentes) — NO asserts de
contenido específico (los datos cambian constantemente, la estructura no
debería).
"""
