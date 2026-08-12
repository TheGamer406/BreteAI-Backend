"""
Conector RemoteOK — API pública. El primer elemento del array de respuesta es
un aviso legal/metadata (no una oferta), se filtra en _fetch(). Requiere un
User-Agent "normal" o la API puede bloquear la request.
"""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.connectors.base import BaseConnector
from app.connectors.canonical import Modalidad, OfertaCanonica

logger = logging.getLogger(__name__)


class RemoteOKConnector(BaseConnector):
    fuente = "remoteok"
    _URL = "https://remoteok.com/api"
    # UA honesto e identificable (proyecto legal-first): la API es pública
    # pero rechaza los UA default de librerías HTTP. Si algún día bloquea
    # este UA, reevaluar la fuente antes que disfrazarse de navegador.
    _HEADERS = {
        "User-Agent": "BreteAI/0.1 (+https://github.com/TheGamer406/BreteAI; job aggregator, 4 req/day)"
    }

    def _fetch(self) -> List[dict]:
        response = requests.get(self._URL, headers=self._HEADERS, timeout=15)
        response.raise_for_status()
        raw_data = response.json()
        # El primer elemento es metadata/aviso legal, no una oferta
        return raw_data[1:] if len(raw_data) > 1 else []

    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        ubicacion = raw_item.get("location", "") or ""
        location_lower = ubicacion.lower()

        modalidad = None
        if "remote" in location_lower or "worldwide" in location_lower:
            modalidad = Modalidad.remoto
        elif "hybrid" in location_lower or "hibrido" in location_lower:
            modalidad = Modalidad.mixto

        # 0 o ausente = no especificado, no asumir 0 como salario real
        salario_min = raw_item.get("salary_min") or None
        salario_max = raw_item.get("salary_max") or None

        fecha_publicacion = None
        if raw_item.get("date"):
            try:
                fecha_publicacion = datetime.fromisoformat(
                    raw_item["date"].replace("Z", "+00:00")
                ).date()
            except ValueError:
                pass

        return OfertaCanonica(
            fuente=self.fuente,
            id_externo=str(raw_item.get("id", "")),
            titulo=raw_item.get("position", ""),
            empresa=raw_item.get("company"),
            ubicacion=ubicacion or None,
            modalidad=modalidad,
            salario_min=salario_min,
            salario_max=salario_max,
            salario_moneda=raw_item.get("salary_currency"),
            descripcion=raw_item.get("description", "") or "",
            url=raw_item.get("url", ""),
            fecha_publicacion=fecha_publicacion,
        )
