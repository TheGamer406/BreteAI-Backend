"""Conector Jobicy — API pública, sin autenticación. Todas las ofertas son remotas."""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.connectors.base import BaseConnector
from app.connectors.canonical import Modalidad, OfertaCanonica

logger = logging.getLogger(__name__)


class JobicyConnector(BaseConnector):
    fuente = "jobicy"
    _URL = "https://jobicy.com/api/v2/remote-jobs"

    def _fetch(self) -> List[dict]:
        response = requests.get(self._URL, timeout=15)
        response.raise_for_status()
        return response.json().get("jobs", [])

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        fecha_publicacion = None
        if raw_item.get("pubDate"):
            try:
                fecha_publicacion = datetime.fromisoformat(
                    raw_item["pubDate"].replace("Z", "+00:00")
                ).date()
            except ValueError:
                pass

        salario_min = raw_item.get("annualSalaryMin") or None
        salario_max = raw_item.get("annualSalaryMax") or None

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=str(raw_item.get("id", "")),
            titulo=raw_item.get("jobTitle", ""),
            empresa=raw_item.get("companyName"),
            ubicacion=raw_item.get("jobGeo"),
            modalidad=Modalidad.remoto,  # todas las ofertas de esta fuente son remotas
            salario_min=salario_min,
            salario_max=salario_max,
            salario_moneda=raw_item.get("salaryCurrency") if (salario_min or salario_max) else None,
            descripcion=raw_item.get("jobDescription") or raw_item.get("jobExcerpt", "") or "",
            url=raw_item.get("url", ""),
            fecha_publicacion=fecha_publicacion,
        )
