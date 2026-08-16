"""
TODO (Fase 2): golden set — detecta regresiones grandes de score contra
Ollama REAL. `docs/design.md` §4-B.

Marcar todo con `@pytest.mark.golden` y registrar el marker en `pytest.ini`
junto a `contract` (y agregarlo al `addopts` de exclusión por defecto):
    addopts = -m "not contract and not golden"
Corre SOLO en el server con GPU, a mano o en un workflow aparte:
    pytest -m golden

Cómo funciona:
- `tests/fixtures/golden_set.json`: 5-10 ofertas reales elegidas a mano, cada
  una con un **rango** de score esperado, no un valor exacto (el modelo es no
  determinista; exigir un número exacto haría el test inútilmente frágil).
  Ejemplos del tipo de caso que debe haber:
    - Junior backend Python remoto, stack del perfil → score alto (>70)
    - Senior/Lead con +5 años obligatorios → score bajo (<40)
    - Puesto totalmente ajeno (ej: enfermería) → score muy bajo (<20)
    - Junior data pero presencial en otro país sin reubicación → score medio
- El test corre `ai.analyzer.analizar_oferta()` de verdad y verifica que el
  score caiga dentro del rango.

Qué detecta: que un cambio de prompt, de modelo (Qwen ↔ Llama) o de perfil
rompa el criterio de puntuación. Sin esto, un cambio de prompt puede degradar
todos los scores en silencio y solo te enterás cuando el correo diario te
manda ofertas malas.

Al implementar, dejar registrado en el README o en el propio JSON con qué
modelo se calibraron los rangos — cambiar de modelo puede exigir recalibrar.
"""
