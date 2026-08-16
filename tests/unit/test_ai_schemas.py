"""
TODO (Fase 2): validación de la salida del LLM. **El test más importante de
la fase** — mitiga el Riesgo #1 de `docs/design.md` §5.

Todos estos casos son SIN red y SIN GPU: se le pasa a
`ai.schemas.parsear_respuesta_llm()` un string como si viniera del modelo.

Casos a cubrir (uno por función, nombres descriptivos):
- JSON válido y completo → devuelve `AnalisisIA` con los campos correctos.
- JSON envuelto en fences de markdown (```json ... ```) → lo recupera igual.
- JSON con preámbulo ("Claro, aquí está el análisis: {...}") → lo recupera.
- JSON truncado a la mitad (respuesta cortada) → lanza `RespuestaIAInvalida`,
  NO devuelve un objeto a medias.
- `score` fuera de rango (150, -10) → **rechaza**. No truncar a 100 ni
  asumir 0: un score inventado corrompe el ranking del correo y el dashboard.
- `score` como string ("85") → decidir al implementar si se coacciona o se
  rechaza, y dejar el test que documente la decisión.
- Campos obligatorios faltantes (sin `resumen`, sin `score`) → rechaza.
- Respuesta vacía o solo texto sin JSON → rechaza.
- Tipos equivocados (`requisitos` como string en vez de lista) → rechaza o
  normaliza; documentar cuál con un test.

Guardar los casos largos como fixtures en `tests/fixtures/ollama/` en vez de
strings gigantes inline (ver el README de esa carpeta).
"""
