"""
TODO (Fase 2): feedback simple del usuario → ajustes de los criterios del
prompt. **NO es re-entrenamiento** (`requirements.md` §5.1, decisión cerrada:
se mantiene simple).

Flujo: el usuario corrige en el portal ("esta oferta no era senior, era
junior" / "este score debería ser más alto") → se guarda una fila en
`feedback_ia` (tabla ya existe: `oferta_id`, `campo`, `valor_ia`,
`valor_correcto`, `nota`) → la próxima corrida arma el prompt incluyendo
esas correcciones como criterios extra.

Qué implementar acá:
- `registrar_correccion(db, oferta_id, campo, valor_ia, valor_correcto,
  nota=None) -> FeedbackIA`: inserta en `feedback_ia`. Lo llamará un endpoint
  del portal en Fase 4; por ahora sirve para sembrar datos a mano.
- `derivar_criterios(db, limite: int = 20) -> list[str]`: lee las correcciones
  más recientes y las convierte en líneas de texto para inyectar en el prompt
  (lo que `prompts.construir_prompt_analisis()` recibe como
  `criterios_extra`). Ejemplo de salida:
    "Si el título dice 'Engineer II' sin pedir +3 años, tratalo como mid, no senior."
    "Ofertas de consultoras que no nombran al cliente final: bajar el score."

Reglas:
- **Tope de criterios** (`limite`): el prompt no puede crecer sin control o
  desborda el contexto del modelo y degrada todo lo demás. Priorizar los más
  recientes / más repetidos.
- Agrupar correcciones repetidas en un solo criterio en vez de repetir 20
  líneas casi iguales.
- Esto NO modifica `perfil.toon` (el perfil es del usuario, el feedback es
  del comportamiento del modelo — no mezclar las dos fuentes).

Se puede dejar para el final de Fase 2: sin feedback acumulado todavía, el
sistema funciona igual (`criterios_extra=None`).
"""
