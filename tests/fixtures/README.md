# Fixtures

Un archivo JSON por fuente con una respuesta **real** guardada (llamada manual
a la API, copiada tal cual). Nombre sugerido: `<fuente>.json` (ej: `remotive.json`).

Usados por `tests/unit/test_canonical_mapping.py` para probar el `_map()` de
cada conector sin hacer llamadas de red. Ver `docs/design.md` §4-A.

No editar a mano el contenido de estos JSON más allá de recortar el array a
2-3 items representativos (uno con salario, uno sin, uno con campos
faltantes) — deben reflejar la forma real de la respuesta.
