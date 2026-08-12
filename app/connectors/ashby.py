"""
Conector Ashby (ATS) — API pública, sin autenticación.
Endpoint: GET https://api.ashbyhq.com/posting-api/job-board/{board_name}

Un board_name por empresa objetivo (app.config.Settings.get_ashby_boards()).
Mismo patrón que greenhouse.py/lever.py: _fetch() itera todos los boards y
junta resultados, etiquetando cada item con su board_name.
"""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.config import get_settings
from app.connectors.base import BaseConnector
from app.connectors.canonical import Modalidad, OfertaCanonica

logger = logging.getLogger(__name__)


class AshbyConnector(BaseConnector):
    fuente = "ashby"
    _URL_TEMPLATE = "https://api.ashbyhq.com/posting-api/job-board/{board_name}"

    def _fetch(self) -> List[dict]:
        settings = get_settings()
        boards = settings.get_ashby_boards()
        if not boards:
            logger.warning("[ashby] Sin boards configurados, nada que traer")
            return []

        todos_los_jobs = []
        for board in boards:
            try:
                response = requests.get(self._URL_TEMPLATE.format(board_name=board), timeout=15)
                response.raise_for_status()
                jobs = response.json().get("jobs", [])
                for job in jobs:
                    job["_board_name"] = board
                todos_los_jobs.extend(jobs)
            except requests.RequestException as e:
                logger.error(f"[ashby] Error en board '{board}': {e}")
                continue

        return todos_los_jobs

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        location = raw_item.get("location") or raw_item.get("locationName")

        modalidad = None
        employment_type = (raw_item.get("employmentType") or "").lower()
        if "remote" in employment_type:
            modalidad = Modalidad.remoto
        elif "hybrid" in employment_type:
            modalidad = Modalidad.mixto

        fecha_publicacion = None
        if raw_item.get("publishedDate"):
            try:
                fecha_publicacion = datetime.fromisoformat(
                    raw_item["publishedDate"].replace("Z", "+00:00")
                ).date()
            except ValueError:
                pass

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=str(raw_item.get("id", "")),
            titulo=raw_item.get("title", ""),
            empresa=raw_item.get("_board_name"),  # TODO: mapear a nombre legible cuando haya config board->nombre
            ubicacion=location,
            modalidad=modalidad,
            # descriptionHtml viene crudo, la limpieza es Fase 2
            descripcion=raw_item.get("descriptionHtml", "") or "",
            url=raw_item.get("jobUrl", ""),
            fecha_publicacion=fecha_publicacion,
        )
