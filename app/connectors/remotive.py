"""Conector Remotive — API pública, sin autenticación."""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.connectors.base import BaseConnector
from app.connectors.canonical import Modalidad, OfertaCanonica

logger = logging.getLogger(__name__)


class RemotiveConnector(BaseConnector):
    fuente = "remotive"
    _URL = "https://remotive.com/api/remote-jobs"

    def _fetch(self) -> List[dict]:
        response = requests.get(self._URL, timeout=15)
        response.raise_for_status()
        return response.json().get("jobs", [])

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        ubicacion = raw_item.get("candidate_required_location", "")
        modalidad = Modalidad.remoto if "worldwide" in ubicacion.lower() or "remote" in ubicacion.lower() else None

        fecha_publicacion = None
        if raw_item.get("publication_date"):
            try:
                fecha_publicacion = datetime.fromisoformat(
                    raw_item["publication_date"].replace("Z", "+00:00")
                ).date()
            except ValueError:
                pass

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=str(raw_item["id"]),
            titulo=raw_item.get("title", ""),
            empresa=raw_item.get("company_name"),
            ubicacion=ubicacion or None,
            modalidad=modalidad,
            # salario: esta fuente casi siempre lo trae como string libre vacío,
            # no se intenta parsear acá — queda None (design.md §4.4)
            descripcion=raw_item.get("description", ""),
            url=raw_item.get("url", ""),
            fecha_publicacion=fecha_publicacion,
        )
