"""
Conector Lever (ATS) — API pública, sin autenticación.
Endpoint: GET https://api.lever.co/v0/postings/{company}?mode=json

Un slug de empresa por empresa objetivo (app.config.Settings.get_lever_companies()).
Mismo patrón que greenhouse.py: _fetch() itera todas las empresas y junta
resultados, etiquetando cada item con su company slug.
"""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.config import get_settings
from app.connectors.base import BaseConnector
from app.connectors.canonical import Modalidad, OfertaCanonica

logger = logging.getLogger(__name__)


class LeverConnector(BaseConnector):
    fuente = "lever"
    _URL_TEMPLATE = "https://api.lever.co/v0/postings/{company}?mode=json"

    def _fetch(self) -> List[dict]:
        settings = get_settings()
        companies = settings.get_lever_companies()
        if not companies:
            logger.warning("[lever] Sin empresas configuradas, nada que traer")
            return []

        todos_los_jobs = []
        for company in companies:
            try:
                response = requests.get(self._URL_TEMPLATE.format(company=company), timeout=15)
                response.raise_for_status()
                jobs = response.json()  # Lever devuelve un array plano
                for job in jobs:
                    job["_company_slug"] = company
                todos_los_jobs.extend(jobs)
            except requests.RequestException as e:
                logger.error(f"[lever] Error en empresa '{company}': {e}")
                continue

        return todos_los_jobs

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        ubicacion = raw_item.get("categories", {}).get("location", "")

        # 'commitment' es tipo de contrato (full-time/part-time), NO modalidad —
        # inferir modalidad de la ubicación/texto, no confundir los dos campos
        modalidad = None
        loc_lower = (ubicacion or "").lower()
        if "remote" in loc_lower or "remoto" in loc_lower:
            modalidad = Modalidad.remoto
        elif "hybrid" in loc_lower or "hibrido" in loc_lower:
            modalidad = Modalidad.mixto

        salary = raw_item.get("salary") or {}

        fecha_publicacion = None
        if raw_item.get("createdAt"):
            try:
                # Lever devuelve createdAt en milisegundos epoch
                fecha_publicacion = datetime.fromtimestamp(raw_item["createdAt"] / 1000).date()
            except (ValueError, TypeError, OSError):
                pass

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=str(raw_item.get("id", "")),
            titulo=raw_item.get("text", ""),
            empresa=raw_item.get("_company_slug"),  # TODO: mapear a nombre legible cuando haya config slug->nombre
            ubicacion=ubicacion or None,
            modalidad=modalidad,
            salario_min=salary.get("min"),
            salario_max=salary.get("max"),
            salario_moneda=salary.get("currency"),
            descripcion=raw_item.get("descriptionPlain") or raw_item.get("description", "") or "",
            url=raw_item.get("hostedUrl", ""),
            fecha_publicacion=fecha_publicacion,
        )
