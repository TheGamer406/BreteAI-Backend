"""Conector Himalayas — API pública, sin autenticación. Todas las ofertas son remotas."""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.connectors.base import BaseConnector
from app.connectors.canonical import Modalidad, OfertaCanonica

logger = logging.getLogger(__name__)


class HimalayasConnector(BaseConnector):
    fuente = "himalayas"
    _URL = "https://himalayas.app/jobs/api"

    def _fetch(self) -> List[dict]:
        response = requests.get(self._URL, timeout=15)
        response.raise_for_status()
        return response.json().get("jobs", [])

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        # pubDate viene como epoch segundos (int), NO como string ISO
        # (confirmado contra la API real 2026-08-12) — no asumir formato de
        # otras fuentes sin verificar.
        fecha_publicacion = None
        if raw_item.get("pubDate"):
            try:
                fecha_publicacion = datetime.fromtimestamp(raw_item["pubDate"]).date()
            except (ValueError, TypeError, OSError):
                pass

        # locationRestrictions vacío o ausente = abierta a cualquier ubicación
        restricciones = raw_item.get("locationRestrictions") or []
        ubicacion = ", ".join(restricciones) if restricciones else None

        salario_min = raw_item.get("minSalary")
        salario_max = raw_item.get("maxSalary")

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=raw_item.get("guid", ""),
            titulo=raw_item.get("title", ""),
            empresa=raw_item.get("companyName"),
            ubicacion=ubicacion,
            modalidad=Modalidad.remoto,  # todas las ofertas de esta fuente son remotas
            salario_min=salario_min,
            salario_max=salario_max,
            salario_moneda=raw_item.get("currency") if (salario_min or salario_max) else None,
            descripcion=raw_item.get("description", "") or "",
            url=raw_item.get("applicationLink", ""),
            fecha_publicacion=fecha_publicacion,
        )
