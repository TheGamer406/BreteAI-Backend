"""
Conector Greenhouse (ATS) — API pública, sin autenticación.
Endpoint confirmado (docs/requirements.md §4.1):
  GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

Un board_token por empresa objetivo (app.config.Settings.get_greenhouse_tokens()).
_fetch() itera todos los tokens y junta los resultados en una sola lista,
etiquetando cada item crudo con su board_token para que _map() sepa de
qué empresa es (la API de Greenhouse no devuelve el nombre de empresa
en el job individual).
"""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.config import get_settings
from app.connectors.base import BaseConnector
from app.connectors.canonical import OfertaCanonica

logger = logging.getLogger(__name__)


class GreenhouseConnector(BaseConnector):
    fuente = "greenhouse"
    _URL_TEMPLATE = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    def _fetch(self) -> List[dict]:
        settings = get_settings()
        tokens = settings.get_greenhouse_tokens()
        if not tokens:
            logger.warning("[greenhouse] Sin board tokens configurados, nada que traer")
            return []

        todos_los_jobs = []
        for token in tokens:
            try:
                response = requests.get(self._URL_TEMPLATE.format(board_token=token), timeout=15)
                response.raise_for_status()
                jobs = response.json().get("jobs", [])
                for job in jobs:
                    job["_board_token"] = token  # para que _map() sepa la empresa
                todos_los_jobs.extend(jobs)
            except requests.RequestException as e:
                logger.error(f"[greenhouse] Error en board '{token}': {e}")
                # No relanzar: un board caído no debe tumbar a los demás boards
                continue

        return todos_los_jobs

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        location = None
        if raw_item.get("location") and raw_item["location"].get("name"):
            location = raw_item["location"]["name"]

        fecha_publicacion = None
        if raw_item.get("updated_at"):
            try:
                fecha_publicacion = datetime.strptime(
                    raw_item["updated_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                ).date()
            except ValueError:
                pass

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=str(raw_item["id"]),
            titulo=raw_item.get("title", ""),
            empresa=raw_item.get("_board_token"),  # TODO: mapear a nombre legible cuando haya config token->nombre
            ubicacion=location,
            # descripcion viene como HTML crudo (campo "content") — la limpieza es Fase 2
            descripcion=raw_item.get("content", "") or "",
            url=raw_item.get("absolute_url", ""),
            fecha_publicacion=fecha_publicacion,
        )
