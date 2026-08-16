"""
TODO (Fase 3): elegir QUÉ ofertas van en el correo. **Empezar por acá.**

Es el paso que define si el correo sirve o es spam: se manda 4 veces al día
(`requirements.md` §4.3), así que si siempre selecciona el mismo top 10 por
score, el usuario recibe el mismo correo cuatro veces y lo empieza a ignorar.

Qué implementar acá:
- `seleccionar_para_correo(db: Session, limite: int = 10, score_minimo: int | None = None) -> list[Oferta]`:
  devuelve las ofertas a incluir, ordenadas por `score` descendente.
  Filtros que debe aplicar:
    1. Solo **no aplicadas** (`requirements.md` §10). Ver decisión abierta abajo.
    2. Con `score` no nulo (las que la IA no pudo analizar no van al correo).
    3. Opcionalmente, `score >= score_minimo`.
    4. **No repetir lo ya enviado** — ver decisión abierta, es la importante.
- `marcar_como_enviadas(db, ofertas) -> Correo`: inserta la fila en `correos`
  (tabla ya existe: `enviado_en`, `oferta_ids BIGINT[]`). Esa tabla es a la
  vez el registro histórico Y la fuente para excluir repetidos en la próxima
  corrida, además de alimentar la vista "último correo" del portal (Fase 4).

Este módulo NO manda correos ni arma HTML: solo consulta y registra. Lo llama
`envio.py` (misma separación que `staging.py` <-> `base.py` en Fase 1).

## Decisiones abiertas (resolver al implementar y DEJARLO ESCRITO en el código)

1. **¿Se re-envían ofertas ya enviadas?** (la decisión más importante de la fase)
   - Opción A: excluir todo lo que ya apareció en algún `correos.oferta_ids`.
     Cada correo trae solo novedades. Riesgo: una oferta con score alto que no
     aplicaste se menciona una sola vez en la vida y se pierde.
   - Opción B: excluir solo lo enviado en las últimas N horas/corridas. Insiste
     con lo bueno sin ser repetitivo.
   - Opción C: no excluir nada (siempre el top N global). Simple, pero el mismo
     correo 4x/día.
   Arrancar por (A) o (B); (C) es la que hace que el correo se vuelva ruido.

2. **¿Qué estados cuentan como "no aplicada"?** Los estados son
   `nueva|vista|aplicada|enProceso|enEspera|respondida|rechazada`
   (`requirements.md` §6). Candidatos: solo `nueva`, o `nueva` + `vista`
   (vista = la abriste pero no aplicaste todavía → tiene sentido recordártela).
   `rechazada` claramente NO va.

3. **¿Score mínimo?** Si en una corrida solo hay ofertas de score 15, ¿se manda
   un correo con basura o no se manda nada? Un umbral (ej. 40) evita entrenar
   al usuario a ignorar el correo. Definirlo como constante acá, no mágico.
"""
