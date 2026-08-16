"""
Registro único de conectores: fuente -> clase. Único lugar del proyecto que
lista qué conectores existen (DRY) — `pipeline/runner.py` lo usa para saber
qué correr en cada corrida, `pipeline/worker.py` lo usa para re-mapear el
`payload` crudo guardado en `ofertas_raw` de vuelta a `OfertaCanonica`
según su `fuente` (el payload es el JSON original, no el canónico —
ver docstring de `connectors/base.py`).
"""

from typing import Type

from app.connectors.adzuna import AdzunaConnector
from app.connectors.arbeitnow import ArbeitnowConnector
from app.connectors.ashby import AshbyConnector
from app.connectors.base import BaseConnector
from app.connectors.greenhouse import GreenhouseConnector
from app.connectors.himalayas import HimalayasConnector
from app.connectors.jobicy import JobicyConnector
from app.connectors.lever import LeverConnector
from app.connectors.remoteok import RemoteOKConnector
from app.connectors.remotive import RemotiveConnector

REGISTRO_CONECTORES: dict[str, Type[BaseConnector]] = {
    "remotive": RemotiveConnector,
    "remoteok": RemoteOKConnector,
    "arbeitnow": ArbeitnowConnector,
    "jobicy": JobicyConnector,
    "himalayas": HimalayasConnector,
    "adzuna": AdzunaConnector,
    "greenhouse": GreenhouseConnector,
    "lever": LeverConnector,
    "ashby": AshbyConnector,
}


def conectores_para_corrida() -> list[BaseConnector]:
    """Instancia todos los conectores registrados, en orden estable."""
    return [cls() for cls in REGISTRO_CONECTORES.values()]
