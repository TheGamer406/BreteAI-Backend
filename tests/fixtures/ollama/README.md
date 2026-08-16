# Fixtures de respuestas de Ollama (Fase 2)

Respuestas **como las devuelve el LLM**, para testear
`app/ai/schemas.py::parsear_respuesta_llm()` sin GPU ni red.

Guardar acá los casos largos (en vez de strings gigantes inline en el test).
Sugeridos, un archivo por caso:

| Archivo | Qué representa |
|---|---|
| `respuesta_valida.json` | JSON limpio y completo — el camino feliz |
| `respuesta_con_fences.txt` | El mismo JSON envuelto en ` ```json ... ``` ` |
| `respuesta_con_preambulo.txt` | "Claro, aquí está el análisis:" + JSON |
| `respuesta_truncada.txt` | JSON cortado a la mitad (límite de tokens) |
| `respuesta_score_invalido.json` | `score: 150` — debe ser rechazada |
| `respuesta_sin_json.txt` | Solo prosa, el modelo ignoró la instrucción |

**Importante:** estos fixtures deben salir de corridas REALES contra el modelo
elegido, no inventados a mano. Los vicios de un 7B local (dónde exactamente
corta, cómo formatea) son específicos del modelo — inventarlos haría que los
tests pasen contra un problema que no es el real.

Al capturarlos, anotar con qué modelo/versión se generaron.
