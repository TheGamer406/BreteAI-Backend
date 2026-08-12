from enum import Enum
from typing import Optional
from datetime import date
from pydantic import BaseModel

class Modalidad(str, Enum):
    """Modalidad de trabajo: presencial, remoto o mixto."""
    presencial = "presencial"
    remoto = "remoto"
    mixto = "mixto"

class OfertaCanonica(BaseModel):
    """
    Modelo canónico para ofertas de trabajo (design.md §2).

    Este es el contrato único que TODOS los conectores deben cumplir.
    Si un conector devuelve instancias válidas de esta clase, puede guardarse
    directamente en la DB sin reinterpretaciones.
    """

    # Identificación (por fuente)
    fuente: str  # "remotive", "greenhouse", "lever", etc.
    id_externo: str  # ID único de la oferta en esa fuente

    # Información principal
    titulo: str
    empresa: Optional[str] = None
    ubicacion: Optional[str] = None
    pais: Optional[str] = None
    modalidad: Optional[Modalidad] = None

    # Salario (campos SUELTOS, no objeto anidado)
    salario_min: Optional[float] = None
    salario_max: Optional[float] = None
    salario_moneda: Optional[str] = None
    salario_estimado: bool = False

    # Descripción y URL
    descripcion: str
    url: str
    fecha_publicacion: Optional[date] = None

    class Config:
        use_enum_values = False  # Mantener enums como objetos, no strings