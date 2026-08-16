"""
TODO (Fase 3): render del HTML del correo. Sin red, sin SMTP, sin DB --
son strings puros (`design.md` §4-C, nivel unitario).

Construir las `Oferta` a mano (no hace falta DB para renderizar). Ojo: son
objetos ORM, así que se pueden instanciar sin sesión mientras no se acceda a
relaciones -- si estorba, definir un pequeño dataclass/stub en el test.

Casos a cubrir:
- 5 ofertas -> el HTML tiene 5 cards, ordenadas por score descendente.
- Cada card incluye: puesto, empresa, score, y el **link al portal** con el
  `oferta.id` correcto (`{portal_base_url}/ofertas/{id}`).
- El `score_razon` (el "match" de `requirements.md` §10) aparece en la card.
- **Salario estimado vs real:** una oferta con `salario_estimado=True` se
  muestra marcada como estimada; una con salario real no. Este test es el que
  evita que el correo presente un número inventado como si lo hubiera
  publicado la empresa.
- **Salario ausente:** aparece "no especificado", nunca "None" ni vacío.
- Oferta con `similar_a` no nulo: se refleja la decisión que se haya tomado
  en `plantilla.py` (ocultar u avisar) -- el test documenta cuál fue.
- El asunto no viene vacío y da idea del contenido (ej. cantidad de ofertas).
- `render_texto_plano()` no contiene tags HTML.
- Lista vacía: decidir si lanza o devuelve algo vacío. En la práctica `envio.py`
  no debería llamarlo con lista vacía (corta antes), pero el test fija el
  contrato.
"""
