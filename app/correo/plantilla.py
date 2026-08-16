"""
TODO (Fase 3): render del HTML del correo. Único lugar del proyecto con
markup de correo (DRY) -- `envio.py` y los tests lo piden acá.

Qué implementar acá:
- `render_correo(ofertas: list[Oferta], portal_base_url: str) -> tuple[str, str]`:
  devuelve `(asunto, cuerpo_html)`.
- Una **card por oferta** (`requirements.md` §10) con: puesto, score, empresa,
  modalidad, salario (si se obtuvo) y **link directo al portal a esa oferta**
  (`{portal_base_url}/ofertas/{oferta.id}`). El `score_razon` que generó la IA
  en Fase 2 es el "match" del que habla el requerimiento -- incluirlo, es lo
  que hace que el correo sea útil y no solo una lista de títulos.
- `render_texto_plano(ofertas, portal_base_url) -> str`: alternativa en texto.
  Un correo HTML sin `text/plain` alternativo cae más fácil en spam, y Gmail
  SMTP es el canal (`requirements.md` §10) -- vale la pena mandarlo multipart.

Reglas de render:
- **Salario:** distinguir visualmente el estimado del real. `ofertas.salario_estimado`
  es `True` cuando lo calculó `ai/salario.py` promediando otras ofertas, no
  cuando lo publicó la empresa. Mostrarlo como "≈ estimado" o similar; mezclarlos
  sin marca engaña al usuario a la hora de decidir si aplica.
- **Salario ausente:** "no especificado", nunca un `None`/vacío crudo en el HTML.
- **Ofertas marcadas como duplicadas** (`ofertas.similar_a` no nulo, viene del
  dedup semántico de Fase 2): decidir si se ocultan o se muestran con un aviso
  "similar a otra oferta". No mandar dos cards casi idénticas sin explicación.
- **CSS inline.** Los clientes de correo (Gmail incluido) ignoran `<style>` en
  `<head>` y no soportan flex/grid de forma confiable. Tablas + estilos inline
  es lo feo pero lo que funciona. No hace falta que sea lindo, sí que se lea
  bien en el celular (es un disparador para ir al portal, §10).
- **Sin imágenes externas ni JS**: se bloquean por defecto y suman puntaje de spam.

`portal_base_url` viene de config (`PORTAL_BASE_URL`). El portal es Fase 4, así
que por ahora los links van a apuntar a algo que todavía no existe: está bien,
la URL se define ya y el portal la respeta cuando se construya.

Testeable sin red ni SMTP: son strings puros (`tests/unit/test_correo_plantilla.py`).
"""
