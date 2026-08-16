"""
TODO (Fase 3): orquesta el envío. Es la etapa 3 del pipeline
(`design.md` §1: `ofertas` -> correo top 5-10).

Qué implementar acá:
- `enviar_correo_ofertas(db: Session, limite: int = 10) -> Correo | None`:
    1. `seleccion.seleccionar_para_correo(db, limite)`.
    2. Si la lista viene vacía -> **no mandar nada** y devolver `None`
       (`requirements.md` §4.3: "si hay resultados → correo"; un correo vacío
       4 veces al día es la forma más rápida de que el usuario lo filtre).
    3. `plantilla.render_correo(ofertas, portal_base_url)`.
    4. `cliente.ClienteSMTP().enviar(...)` al `MAIL_TO` de config.
    5. `seleccion.marcar_como_enviadas(db, ofertas)` -> fila en `correos`.
       **Solo después de que el envío salió bien**: si se registra antes y el
       SMTP falla, esas ofertas quedan marcadas como enviadas sin que el
       usuario las haya visto nunca, y no vuelven a aparecer.
- `enviar_alerta_conectores(db, fuentes_rotas: list[str]) -> None` (opcional,
  puede ir al final): el canal real de la alerta que hoy solo loguea
  `alerts/connector_health.py` (su docstring lo deja anotado como TODO de
  Fase 3, y `requirements.md` §4.5 lo pide). Decidir: ¿correo aparte, o una
  sección al pie del correo de ofertas? Un correo aparte por cada conector
  roto en cada corrida es ruido; una línea al pie no se lee. Anotarlo.

Reglas:
- Un fallo de SMTP **no debe tumbar la corrida** ni perder datos: las ofertas
  ya están en `ofertas`, el correo es solo la notificación. Loguear el error y
  seguir (mismo criterio de aislamiento que los conectores en Fase 1 y el
  worker en Fase 2).
- Este módulo no arma HTML ni hace queries directas: compone `seleccion` +
  `plantilla` + `cliente`. Si termina con SQL o markup adentro, algo se filtró
  de la capa equivocada.
- Lo llama `scheduler/jobs.py` como paso 3, después del worker de IA.
"""
