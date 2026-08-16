"""
TODO (Fase 2): construcción de los prompts que se le mandan a Ollama.

Qué implementar acá:
- `construir_prompt_analisis(oferta: OfertaCanonica, perfil: Perfil,
  criterios_extra: list[str] | None = None) -> str`:
  arma el prompt que pide resumen + extracción + score. Debe incluir:
    1. Rol/instrucción del sistema (analista de ofertas, responde SOLO JSON).
    2. El perfil del candidato (de `perfil.py`).
    3. Los criterios de match (`criterios_match` del perfil: pesos,
       `penalizar[]`, `bonificar[]`).
    4. `criterios_extra`: los ajustes derivados del feedback del usuario
       (ver `app/feedback/criterios.py`) — así las correcciones afinan el
       prompt sin re-entrenar nada (`requirements.md` §5.1).
    5. La oferta a analizar (titulo, empresa, ubicacion, modalidad,
       descripcion; la descripción puede venir en HTML crudo desde los ATS —
       limpiarla acá antes de meterla al prompt, no mandar tags al modelo).
    6. El schema JSON exacto que debe devolver (mismos campos que
       `ai/schemas.py`, con ejemplo de formato).
- `construir_prompt_salario(oferta) -> str` (opcional, ver `salario.py`).

Reglas:
- **Descripciones largas:** truncar a un límite razonable de caracteres antes
  de mandarlas (una oferta de Greenhouse puede traer 20k+ caracteres de HTML
  y desbordar el contexto del modelo). Definir el límite como constante acá.
- **Idioma:** las ofertas vienen en inglés y español; el resumen debe salir en
  español (es para el usuario). Decirlo explícito en el prompt.
- **Un solo lugar para el texto del prompt.** Si `analyzer.py` o los tests
  necesitan el prompt, lo piden acá — no se arman strings de prompt en otro
  archivo (DRY, y hace que el golden set sea reproducible).

Testeable sin GPU: estas funciones son strings puros, se testean comparando
que el prompt contenga el perfil y los criterios esperados
(`tests/unit/test_prompts.py`).
"""
