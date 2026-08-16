"""
Reintentos con backoff exponencial, compartido entre los conectores de
Fase 1 (`app/connectors/base.py`) y el cliente de IA de Fase 2
(`app/ai/client.py`) — la misma lógica no se duplica en cada uno (DRY).
"""

import logging
import time
from typing import Callable, Optional, TypeVar

T = TypeVar("T")

MAX_REINTENTOS_DEFAULT = 3
BACKOFF_BASE_SEGUNDOS_DEFAULT = 2  # 2s, 4s, 8s...


def reintentar_con_backoff(
    func: Callable[[], T],
    *,
    max_intentos: int = MAX_REINTENTOS_DEFAULT,
    backoff_base_segundos: int = BACKOFF_BASE_SEGUNDOS_DEFAULT,
    etiqueta: str = "",
    logger: Optional[logging.Logger] = None,
) -> T:
    """Ejecuta `func()` reintentando ante cualquier excepción, con backoff
    exponencial (`backoff_base_segundos ** intento`). Si se agotan los
    intentos, propaga la última excepción -- el llamador decide qué hacer
    (ej: marcar un conector o el cliente de IA como fallido sin tumbar el
    resto del proceso)."""
    log = logger or logging.getLogger(__name__)
    ultimo_error: Optional[Exception] = None

    for intento in range(1, max_intentos + 1):
        try:
            return func()
        except Exception as e:
            ultimo_error = e
            if intento < max_intentos:
                espera = backoff_base_segundos**intento
                log.warning(
                    f"{etiqueta} intento {intento}/{max_intentos} falló: {e}. "
                    f"Reintentando en {espera}s..."
                )
                time.sleep(espera)
            else:
                log.error(f"{etiqueta} falló tras {max_intentos} intentos: {e}")

    assert ultimo_error is not None
    raise ultimo_error
