"""Conector Arbeitnow — API pública, sin autenticación."""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.connectors.base import BaseConnector
from app.connectors.canonical import Modalidad, OfertaCanonica

logger = logging.getLogger(__name__)


class ArbeitnowConnector(BaseConnector):
    fuente = "arbeitnow"
    _URL = "https://www.arbeitnow.com/api/job-board-api"

    def _fetch(self) -> List[dict]:
        response = requests.get(self._URL, timeout=15)
        response.raise_for_status()
        # Paginado ("links.next"); para el volumen de este proyecto, la
        # primera página alcanza — ampliar a paginación completa si hace falta más volumen.
        return response.json().get("data", [])

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        modalidad = Modalidad.remoto if raw_item.get("remote") else None

        fecha_publicacion = None
        if raw_item.get("created_at"):
            try:
                fecha_publicacion = datetime.fromtimestamp(raw_item["created_at"]).date()
            except (ValueError, TypeError, OSError):
                pass

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=raw_item.get("slug", ""),
            titulo=raw_item.get("title", ""),
            empresa=raw_item.get("company_name"),
            ubicacion=raw_item.get("location"),
            modalidad=modalidad,
            # Esta fuente no publica salario
            descripcion=raw_item.get("description", "") or "",
            url=raw_item.get("url", ""),
            fecha_publicacion=fecha_publicacion,
        )
