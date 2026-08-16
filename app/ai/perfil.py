"""
Carga y parseo de `resources/perfil.toon` (el perfil del candidato que la
IA usa como contexto para puntuar cada oferta).

TOON es un formato compacto tipo YAML con arrays tipados. El parser de acá
cubre SOLO el subconjunto que usa `config/perfil.example.toon`:
  - `clave: valor`               -> escalar (bool/int/float/str, se infiere)
  - `clave:` (sin nada más)      -> bloque anidado (líneas indentadas debajo)
  - `clave[N]: a, b, c`          -> lista inline de strings
  - `clave[N]{f1,f2}:` + filas   -> lista de objetos (una fila CSV por línea)
Si este parser empieza a crecer para cubrir más casos, es señal de que
convenía otro formato -- no seguir agrandándolo en silencio (ver docstring
original de este archivo en el esqueleto).

Limitación conocida: las filas de tabla (`experiencia`, `formacion`, etc.)
se separan por coma sin soporte de comillas -- si un campo como `detalle`
necesita una coma literal, hay que evitarla en el TOON o extender el parser.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel

from app.config import get_settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]  # BreteAI-Backend/


class PerfilNoEncontrado(Exception):
    """resources/perfil.toon no existe. Copiar config/perfil.example.toon
    a resources/perfil.toon y completarlo con datos reales (privados,
    gitignored) antes de correr el pipeline de IA."""


# --- modelo --------------------------------------------------------------


class Candidato(BaseModel):
    nombre: str
    email: str
    telefono: str
    linkedin: str
    ubicacion: str
    seniority: str
    resumen: str


class Idioma(BaseModel):
    idioma: str
    nivel: str


class SkillsTecnicos(BaseModel):
    lenguajes: list[str] = []
    web: list[str] = []
    documentacion_diseno: list[str] = []
    ia: list[str] = []


class Experiencia(BaseModel):
    empresa: str
    rol: str
    periodo: str
    detalle: str


class Formacion(BaseModel):
    institucion: str
    titulo: str
    periodo: str


class SalarioPreferencia(BaseModel):
    moneda: str
    actual: float
    minimo_neto: float
    ideal_neto: float
    tope_ideal_neto: float
    nota: str


class Preferencias(BaseModel):
    modalidades: list[str] = []
    ubicaciones_aceptadas: list[str] = []
    reubicacion_internacional: bool = False
    salario: SalarioPreferencia
    keywords: list[str] = []
    excluir: list[str] = []


class CriteriosMatch(BaseModel):
    peso_skills: str
    peso_seniority: str
    peso_salario: str
    peso_modalidad: str
    penalizar: list[str] = []
    bonificar: list[str] = []


class Perfil(BaseModel):
    candidato: Candidato
    idiomas: list[Idioma] = []
    intereses_rol: list[str] = []
    skills_tecnicos: SkillsTecnicos
    experiencia: list[Experiencia] = []
    formacion: list[Formacion] = []
    soft_skills: list[str] = []
    preferencias: Preferencias
    criterios_match: CriteriosMatch


# --- parser TOON -----------------------------------------------------------

_NESTED = object()  # sentinel: la línea abre un bloque anidado


class _TableHeader:
    def __init__(self, fields: list[str]):
        self.fields = fields


_LINE_RE = re.compile(
    r"^(?P<key>\w+)(\[(?P<n>\d+)\])?(\{(?P<fields>[\w,]+)\})?:\s*(?P<rest>.*)$"
)


def _coerce_scalar(s: str) -> Union[bool, int, float, str]:
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _parse_line(content: str):
    m = _LINE_RE.match(content)
    if not m:
        raise ValueError(f"Línea TOON no reconocida: {content!r}")
    key = m.group("key")
    fields = m.group("fields")
    rest = m.group("rest")
    n = m.group("n")

    if fields:
        return key, _TableHeader(fields.split(","))
    if not rest:
        return key, _NESTED
    if n:  # lista inline: clave[N]: a, b, c
        return key, [x.strip() for x in rest.split(",")]
    return key, _coerce_scalar(rest)


def parse_toon(texto: str) -> dict:
    """Parsea un documento TOON (subconjunto descrito arriba) a dict anidado."""
    lines: list[tuple[int, str]] = []
    for raw in texto.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))

    pos = 0

    def parse_block(indent_level: int) -> dict:
        nonlocal pos
        result: dict = {}
        while pos < len(lines) and lines[pos][0] >= indent_level:
            cur_indent, content = lines[pos]
            if cur_indent > indent_level:
                # Indentación inesperada (no debería pasar con un TOON bien
                # formado); se ignora la línea para no romper todo el parseo.
                pos += 1
                continue
            pos += 1
            key, value = _parse_line(content)

            if value is _NESTED:
                if pos < len(lines) and lines[pos][0] > indent_level:
                    result[key] = parse_block(lines[pos][0])
                else:
                    result[key] = {}
            elif isinstance(value, _TableHeader):
                rows = []
                if pos < len(lines) and lines[pos][0] > indent_level:
                    child_indent = lines[pos][0]
                    while pos < len(lines) and lines[pos][0] == child_indent:
                        row_line = lines[pos][1]
                        pos += 1
                        parts = [p.strip() for p in row_line.split(",")]
                        rows.append(dict(zip(value.fields, parts)))
                result[key] = rows
            else:
                result[key] = value
        return result

    return parse_block(0)


# --- carga -------------------------------------------------------------


def _resolver_ruta_perfil(ruta: Optional[Path]) -> Path:
    if ruta is not None:
        return Path(ruta)
    configurada = Path(get_settings().perfil_path)
    if configurada.is_absolute():
        return configurada
    return (BACKEND_ROOT / configurada).resolve()


@lru_cache
def cargar_perfil(ruta: Optional[Path] = None) -> Perfil:
    """Lee y parsea el perfil. Cacheado -- se lee una sola vez por proceso,
    no una vez por oferta (el worker procesa cientos)."""
    ruta_final = _resolver_ruta_perfil(ruta)

    if not ruta_final.exists():
        raise PerfilNoEncontrado(
            f"No se encontró el perfil en {ruta_final}. "
            f"Copiá config/perfil.example.toon a resources/perfil.toon y completalo."
        )

    texto = ruta_final.read_text(encoding="utf-8")
    datos = parse_toon(texto)
    return Perfil.model_validate(datos)
