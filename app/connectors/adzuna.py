"""
Conector Adzuna — requiere credenciales (gratis, 1k llamadas/mes).
Endpoint: GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
  ?app_id=...&app_key=...&results_per_page=...

Cuidado con la cuota mensual: se consulta 1 sola página por país configurado,
1 sola vez por corrida (no se pagina completo para no agotar los 1k/mes con
4 corridas/día). Países a consultar: TODO ajustar según perfil.toon
(CR + apertura a reubicación internacional) — por ahora hardcodeado a un
país de referencia hasta que se defina la lista completa.
"""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.config import get_settings
from app.connectors.base import BaseConnector
from app.connectors.canonical import OfertaCanonica

logger = logging.getLogger(__name__)

# TODO Fase 1: mover a config/perfil cuando se defina la lista completa de
# países objetivo (perfil abierto a reubicación internacional).
PAISES_ADZUNA = ["us", "gb"]
RESULTADOS_POR_PAGINA = 50


class AdzunaConnector(BaseConnector):
    fuente = "adzuna"
    _URL_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"

    def _fetch(self) -> List[dict]:
        settings = get_settings()
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            logger.warning("[adzuna] Sin credenciales configuradas (ADZUNA_APP_ID/APP_KEY), nada que traer")
            return []

        todos_los_jobs = []
        for country in PAISES_ADZUNA:
            try:
                params = {
                    "app_id": settings.adzuna_app_id,
                    "app_key": settings.adzuna_app_key,
                    "results_per_page": RESULTADOS_POR_PAGINA,
                }
                response = requests.get(
                    self._URL_TEMPLATE.format(country=country), params=params, timeout=15
                )
                response.raise_for_status()
                jobs = response.json().get("results", [])
                for job in jobs:
                    job["_country"] = country
                todos_los_jobs.extend(jobs)
            except requests.RequestException as e:
                logger.error(f"[adzuna] Error en país '{country}': {e}")
                continue

        return todos_los_jobs

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        empresa = None
        if raw_item.get("company"):
            empresa = raw_item["company"].get("display_name")

        ubicacion = None
        if raw_item.get("location"):
            ubicacion = raw_item["location"].get("display_name")

        fecha_publicacion = None
        if raw_item.get("created"):
            try:
                fecha_publicacion = datetime.fromisoformat(
                    raw_item["created"].replace("Z", "+00:00")
                ).date()
            except ValueError:
                pass

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=str(raw_item.get("id", "")),
            titulo=raw_item.get("title", ""),
            empresa=empresa,
            ubicacion=ubicacion,
            pais=raw_item.get("_country"),
            salario_min=raw_item.get("salary_min"),
            salario_max=raw_item.get("salary_max"),
            # La moneda depende del país consultado, no siempre USD — dejar
            # que Fase 2 la infiera del país si hace falta más precisión.
            descripcion=raw_item.get("description", "") or "",
            url=raw_item.get("redirect_url", ""),
            fecha_publicacion=fecha_publicacion,
        )
