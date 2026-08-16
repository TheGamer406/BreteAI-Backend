"""
Render del HTML/texto del correo. Único lugar del proyecto con markup de
correo -- `envio.py` y los tests lo piden acá (DRY).

CSS inline, sin `<style>`, sin flex/grid, sin imágenes externas ni JS: los
clientes de correo (Gmail incluido) los ignoran o bloquean.
"""

from typing import Optional

from app.db.models import Oferta

MODALIDAD_LABELS = {
    "presencial": "Presencial",
    "remoto": "Remoto",
    "mixto": "Mixto",
}


def _formatear_salario(oferta: Oferta) -> str:
    if oferta.salario_min is None and oferta.salario_max is None:
        return "no especificado"

    moneda = oferta.salario_moneda or ""
    if oferta.salario_min is not None and oferta.salario_max is not None:
        texto = f"{moneda} {oferta.salario_min:,.0f} - {oferta.salario_max:,.0f}".strip()
    else:
        monto = oferta.salario_min if oferta.salario_min is not None else oferta.salario_max
        texto = f"{moneda} {monto:,.0f}".strip()

    # No mezclar salario real con estimado sin marcarlo -- el estimado sale
    # de un promedio calculado en Fase 2 (ai/salario.py), no de la empresa.
    if oferta.salario_estimado:
        texto += " (estimado)"
    return texto


def _card_html(oferta: Oferta, portal_base_url: str) -> str:
    url_portal = f"{portal_base_url}/ofertas/{oferta.id}"
    modalidad = MODALIDAD_LABELS.get(oferta.modalidad or "", oferta.modalidad or "no especificada")

    aviso_similar = ""
    if oferta.similar_a is not None:
        aviso_similar = (
            '<p style="margin:4px 0 0;font-size:12px;color:#b45309;">'
            "&#9888; Similar a otra oferta ya vista</p>"
        )

    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid #e5e7eb;border-radius:8px;margin-bottom:16px;">
      <tr>
        <td style="padding:16px;font-family:Arial,Helvetica,sans-serif;">
          <p style="margin:0 0 4px;font-size:16px;font-weight:bold;color:#111827;">{oferta.titulo}</p>
          <p style="margin:0 0 8px;font-size:14px;color:#6b7280;">
            {oferta.empresa or "Empresa no especificada"} &middot; {modalidad}
          </p>
          <p style="margin:0 0 8px;font-size:14px;color:#111827;">
            <strong>Score: {oferta.score}/100</strong> &mdash; {oferta.score_razon or ""}
          </p>
          <p style="margin:0 0 12px;font-size:14px;color:#374151;">
            Salario: {_formatear_salario(oferta)}
          </p>
          {aviso_similar}
          <a href="{url_portal}"
             style="display:inline-block;margin-top:8px;padding:8px 16px;background:#2563eb;
                    color:#ffffff;text-decoration:none;border-radius:6px;font-size:14px;">
            Ver en el portal
          </a>
        </td>
      </tr>
    </table>
    """


def _seccion_alertas_html(fuentes_con_problemas: list[str]) -> str:
    if not fuentes_con_problemas:
        return ""
    lista = ", ".join(fuentes_con_problemas)
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="margin-top:24px;border-top:1px solid #e5e7eb;padding-top:12px;">
      <tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#b91c1c;">
        &#9888; Estas fuentes vienen fallando en las últimas corridas: {lista}
      </td></tr>
    </table>
    """


def render_correo(
    ofertas: list[Oferta],
    portal_base_url: str,
    fuentes_con_problemas: Optional[list[str]] = None,
) -> tuple[str, str]:
    """Devuelve (asunto, cuerpo_html). Las cards se renderizan en el orden
    recibido -- ordenar es responsabilidad de seleccion.py."""
    if not ofertas:
        raise ValueError("render_correo() no debe llamarse con una lista vacía -- envio.py corta antes")

    asunto = f"BreteAI: {len(ofertas)} oferta{'s' if len(ofertas) != 1 else ''} para revisar"
    cards = "".join(_card_html(o, portal_base_url) for o in ofertas)
    alertas = _seccion_alertas_html(fuentes_con_problemas or [])

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f3f4f6;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:24px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0">
        <tr><td style="font-family:Arial,Helvetica,sans-serif;">
          <h2 style="color:#111827;">Tus mejores ofertas de hoy</h2>
          {cards}
          {alertas}
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    return asunto, html


def render_texto_plano(ofertas: list[Oferta], portal_base_url: str) -> str:
    if not ofertas:
        raise ValueError("render_texto_plano() no debe llamarse con una lista vacía")

    lineas = ["Tus mejores ofertas de hoy:", ""]
    for oferta in ofertas:
        lineas.append(
            f"- {oferta.titulo} en {oferta.empresa or 'empresa no especificada'} "
            f"(score {oferta.score}/100)"
        )
        lineas.append(f"  {portal_base_url}/ofertas/{oferta.id}")
        lineas.append("")
    return "\n".join(lineas)
