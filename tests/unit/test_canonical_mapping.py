"""
TODO (Fase 1): un test por conector que valida `_map()` contra su fixture.

Patrón (DRY vía parametrización, NO copiar el mismo test 9 veces):
- Parametrizar sobre (conector_class, fixture_path) para los 9 conectores en
  `app/connectors/` y correr el mismo cuerpo de test para todos:
  1. Cargar el fixture JSON de `tests/fixtures/<fuente>.json`.
  2. Llamar `conector._map(item)` por cada item del fixture.
  3. Assert: el resultado es una instancia válida de `OfertaCanonica`
     (Pydantic valida tipos solo); campos obligatorios (titulo, empresa,
     url, fuente, id_externo) nunca None/vacíos.

Sin red — no debe haber ningún `httpx`/`requests` real en este archivo.
"""
