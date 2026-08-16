"""
TODO (Fase 2): orquesta el análisis de UNA oferta. Es el "template method"
de la capa de IA, equivalente a lo que `connectors/base.py` es para Fase 1.

Qué implementar acá:
- `analizar_oferta(oferta: OfertaCanonica, perfil: Perfil,
  criterios_extra: list[str] | None = None) -> AnalisisIA`:
    1. `prompts.construir_prompt_analisis(...)`
    2. `client.OllamaClient().generar(prompt, formato_json=True)`
    3. `schemas.parsear_respuesta_llm(texto)` → `AnalisisIA` validado
    4. si el parseo falla → reintentar N veces (el modelo es no determinista,
       un reintento suele arreglar un JSON roto). Tras agotar reintentos,
       propagar `RespuestaIAInvalida` para que el worker marque la raw en
       `error` y se pueda reprocesar después.
- `MAX_REINTENTOS_PARSEO = 2` (constante acá, no mágica en el código).

Reglas:
- Este módulo **no toca la DB**. Recibe una oferta canónica, devuelve un
  análisis validado. Persistir es responsabilidad de `pipeline/worker.py`
  (misma separación que `connectors/base.py` ↔ `pipeline/staging.py`).
- Este módulo **no sabe de `ofertas_raw`** ni de estados de procesamiento.
- Log de cuánto tardó cada análisis (útil para calibrar si el modelo elegido
  aguanta el volumen de 4 corridas diarias).

Opcional en esta fase, evaluar al implementar: procesar en lote (varias
ofertas por prompt) para amortizar la latencia. Ojo: subir el batch aumenta
la probabilidad de JSON malformado, que es el Riesgo #1. Si se hace, que sea
detrás de un flag y con el mismo `schemas.py` validando cada elemento.
"""
