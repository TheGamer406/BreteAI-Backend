"""
TODO (Fase 2): schema Pydantic de la SALIDA del LLM. **Empezar por acá.**

Este archivo es la mitigación del **Riesgo #1** de `docs/design.md` §5: un
modelo 7B local va a devolver JSON malformado con frecuencia. Nada de lo que
diga el LLM entra a la DB sin pasar por esta validación.

Qué implementar acá:
- `class AnalisisIA(BaseModel)` con los campos que el LLM debe devolver, que
  son exactamente los que la capa de IA llena en la tabla `ofertas`
  (ver `app/db/models.py` clase `Oferta`, sección "Campos de IA"):
    resumen: str
    requisitos: list[str]
    beneficios: list[str]
    seniority: str | None        # junior | mid | senior | None
    empresa_real: str | None     # "info de segunda mano" (requirements.md §5.1)
    score: int                   # 0-100, con `Field(ge=0, le=100)`
    score_razon: str             # por qué ese score (para el feedback del usuario)
- Validadores estrictos: `score` fuera de rango debe **rechazar**, no truncar
  ni asumir un default (un score inventado es peor que no tener score).
- `def parsear_respuesta_llm(texto: str) -> AnalisisIA`: recibe el texto CRUDO
  del modelo y devuelve el objeto validado. Debe tolerar los vicios típicos
  de un LLM local:
    - JSON envuelto en ```json ... ``` (fences de markdown)
    - texto de preámbulo antes del JSON ("Claro, aquí está el análisis:")
    - JSON truncado a la mitad (respuesta cortada por límite de tokens)
  y lanzar una excepción propia (ej: `RespuestaIAInvalida`) cuando no se puede
  recuperar nada usable. Esa excepción es la que `app/pipeline/worker.py`
  atrapa para marcar la raw como `error` y reintentarla después.

DRY: este es el ÚNICO lugar que sabe qué forma tiene la salida del LLM.
Ni `analyzer.py` ni `worker.py` deben parsear JSON del modelo por su cuenta.

NO poner acá: los campos canónicos (titulo, empresa, url...) — esos NO los
inventa la IA, vienen del raw guardado en Fase 1. Si el LLM devuelve un
titulo distinto, se ignora: el dato de la fuente manda.
"""
