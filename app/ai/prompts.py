"""
Construcción de los prompts que se le mandan al LLM. Único lugar del
proyecto con texto de prompt -- analyzer.py y los tests lo piden acá.
"""

import html
import re

from app.ai.perfil import Perfil
from app.connectors.canonical import OfertaCanonica

# Una oferta de Greenhouse/Ashby puede traer 20k+ caracteres de HTML crudo.
# Se trunca para no desbordar el contexto del modelo (y porque más allá de
# esto ya es boilerplate legal/beneficios repetidos, no señal nueva).
MAX_DESCRIPCION_CHARS = 6000

_TAG_RE = re.compile(r"<[^>]+>")
_BLOQUE_RE = re.compile(r"</?(p|div|br|li|ul|ol|h[1-6])[^>]*>", re.IGNORECASE)
_ESPACIOS_RE = re.compile(r"[ \t]+")
_LINEAS_VACIAS_RE = re.compile(r"\n{3,}")


def _limpiar_descripcion(texto: str) -> str:
    """Quita tags HTML (conservando saltos de línea en elementos de bloque)
    y trunca. No es un parser HTML completo -- suficiente para que el LLM
    reciba texto legible en vez de markup."""
    if not texto:
        return "(sin descripción)"

    texto = _BLOQUE_RE.sub("\n", texto)
    texto = _TAG_RE.sub("", texto)
    texto = html.unescape(texto)
    texto = _ESPACIOS_RE.sub(" ", texto)
    texto = _LINEAS_VACIAS_RE.sub("\n\n", texto).strip()

    if len(texto) > MAX_DESCRIPCION_CHARS:
        texto = texto[:MAX_DESCRIPCION_CHARS] + "\n[...descripción truncada...]"
    return texto


def _seccion_perfil(perfil: Perfil) -> str:
    st = perfil.skills_tecnicos
    skills = ", ".join(st.lenguajes + st.web + st.documentacion_diseno + st.ia)
    pref = perfil.preferencias

    return f"""## Perfil del candidato
- Seniority: {perfil.candidato.seniority}
- Resumen: {perfil.candidato.resumen}
- Intereses de rol: {", ".join(perfil.intereses_rol)}
- Skills técnicos: {skills}
- Modalidades aceptadas: {", ".join(pref.modalidades)}
- Ubicaciones aceptadas: {", ".join(pref.ubicaciones_aceptadas)} (reubicación internacional: {"sí" if pref.reubicacion_internacional else "no"})
- Salario objetivo ({pref.salario.moneda}): mínimo neto {pref.salario.minimo_neto}, ideal neto {pref.salario.ideal_neto}
- Keywords positivas: {", ".join(pref.keywords)}
- Excluir si: {", ".join(pref.excluir)}"""


def _seccion_criterios(perfil: Perfil, criterios_extra: list[str] | None) -> str:
    cm = perfil.criterios_match
    base = f"""## Criterios de match
- Peso skills: {cm.peso_skills}
- Peso seniority: {cm.peso_seniority}
- Peso salario: {cm.peso_salario}
- Peso modalidad: {cm.peso_modalidad}
- Penalizar: {", ".join(cm.penalizar)}
- Bonificar: {", ".join(cm.bonificar)}"""

    if criterios_extra:
        extra = "\n".join(f"- {c}" for c in criterios_extra)
        base += f"\n\n## Ajustes de criterios (de correcciones previas del usuario)\n{extra}"

    return base


def construir_prompt_analisis(
    oferta: OfertaCanonica,
    perfil: Perfil,
    criterios_extra: list[str] | None = None,
) -> str:
    """Arma el prompt de análisis para UNA oferta: perfil + criterios +
    oferta + el schema JSON exacto que se le pide al modelo."""
    descripcion = _limpiar_descripcion(oferta.descripcion)
    modalidad = oferta.modalidad.value if oferta.modalidad else "no especificada"

    return f"""Sos un analista experto en reclutamiento técnico. Tu tarea es analizar UNA
oferta de trabajo y compararla contra el perfil de un candidato, para decidir
qué tan buen match es.

{_seccion_perfil(perfil)}

{_seccion_criterios(perfil, criterios_extra)}

## Oferta a analizar
- Título: {oferta.titulo}
- Empresa: {oferta.empresa or "no especificada"}
- Ubicación: {oferta.ubicacion or "no especificada"}
- Modalidad: {modalidad}
- Descripción:
{descripcion}

## Instrucciones
Respondé SOLO con un objeto JSON (nada de texto antes o después, nada de
fences de markdown), en ESPAÑOL, con exactamente estos campos:

{{
  "resumen": "2-3 líneas resumiendo la oferta, en español",
  "requisitos": ["lista de requisitos clave extraídos de la descripción"],
  "beneficios": ["lista de beneficios mencionados, [] si no hay ninguno"],
  "seniority": "junior, mid o senior según lo que pide la oferta (null si no se puede inferir)",
  "empresa_real": "si detectás que quien publica es un proveedor/consultora y no el cliente final, el nombre del cliente si se menciona; si no aplica, null",
  "score": "número entero 0-100: qué tan buen match es esta oferta para ESTE candidato",
  "score_razon": "1-2 líneas explicando por qué ese score, en español"
}}"""
