"""
Clase base abstracta para todos los conectores. Acá vive TODA la lógica
compartida (fetch con reintentos/backoff, guardado en ofertas_raw, logging,
manejo de errores) — ningún conector individual reimplementa esto (DRY).

Cada conector concreto SOLO implementa:
- atributo de clase `fuente: str`
- `_fetch(self) -> list[dict]`: llamada HTTP cruda a su API.
- `_map(self, raw_item: dict) -> OfertaCanonica | None`: mapea un item crudo
  al modelo canónico (sirve para VALIDAR el item, no para lo que se guarda).
  Retorna None si el item debe descartarse.

Importante: lo que se persiste en `ofertas_raw.payload` es el `raw_item`
ORIGINAL (JSON crudo tal cual vino de la fuente, design.md §1) — el modelo
canónico solo se usa acá para validar que el item tiene los campos mínimos
antes de guardarlo, nunca se guarda el canónico en vez del crudo.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.orm import Session

from app.connectors.canonical import OfertaCanonica
from app.pipeline.staging import guardar_raw

logger = logging.getLogger(__name__)

MAX_REINTENTOS = 3
BACKOFF_BASE_SEGUNDOS = 2  # 2s, 4s, 8s


class BaseConnector(ABC):
    """Template method: run() orquesta fetch -> map -> guardar, las subclases no lo tocan."""

    fuente: str  # cada subclase lo define, ej: "remotive"

    @abstractmethod
    def _fetch(self) -> List[dict]:
        """Llamada HTTP cruda a la API de la fuente. Sin reintentos acá —
        eso lo maneja run(). Debe lanzar excepción si la llamada falla."""
        raise NotImplementedError

    @abstractmethod
    def _map(self, raw_item: dict) -> Optional[OfertaCanonica]:
        """Mapea un item crudo al modelo canónico, solo para VALIDAR que
        tiene los campos mínimos (titulo, descripcion, url, id_externo).
        Retorna None si el item no es mapeable/válido (no lanzar excepción
        por eso, solo para errores reales de parsing irrecuperables)."""
        raise NotImplementedError

    def run(self, db: Session, corrida_id: int) -> dict:
        """
        Orquesta: fetch (con reintentos/backoff) -> valida cada item con
        _map() -> guarda el raw_item ORIGINAL en ofertas_raw (vía staging,
        con idempotencia). Items que fallan el mapeo se loguean y se saltan,
        no tumban el resto del conector.

        Returns:
            dict con {"ok": int, "descartados": int} — cantidad de items
            guardados vs. descartados por fallo de validación/mapeo.
        """
        raw_items = self._fetch_con_reintentos()

        ok = 0
        descartados = 0
        for raw_item in raw_items:
            try:
                oferta = self._map(raw_item)
                if oferta is None:
                    descartados += 1
                    continue

                # Se guarda el raw_item ORIGINAL, no el canónico — el canónico
                # solo sirvió para validar fuente/id_externo/campos mínimos.
                guardar_raw(
                    db=db,
                    corrida_id=corrida_id,
                    fuente=oferta.fuente,
                    id_externo=oferta.id_externo,
                    payload=raw_item,
                )
                ok += 1
            except Exception as e:
                logger.warning(f"[{self.fuente}] Item descartado por error de mapeo: {e}")
                descartados += 1
                continue

        logger.info(f"[{self.fuente}] {ok}/{len(raw_items)} ofertas guardadas ({descartados} descartadas)")
        return {"ok": ok, "descartados": descartados}

    def _fetch_con_reintentos(self) -> List[dict]:
        """Reintentos con backoff exponencial ante error de red/rate limit
        (docs/requirements.md §4.5). Tras agotar los reintentos, propaga la
        excepción para que runner.py marque este conector como fallido sin
        tumbar la corrida completa."""
        ultimo_error = None
        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                return self._fetch()
            except Exception as e:
                ultimo_error = e
                if intento < MAX_REINTENTOS:
                    espera = BACKOFF_BASE_SEGUNDOS ** intento
                    logger.warning(
                        f"[{self.fuente}] Intento {intento}/{MAX_REINTENTOS} falló: {e}. "
                        f"Reintentando en {espera}s..."
                    )
                    time.sleep(espera)
                else:
                    logger.error(f"[{self.fuente}] Falló tras {MAX_REINTENTOS} intentos: {e}")
        raise ultimo_error
