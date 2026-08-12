import logging
from datetime import datetime
from app.db.models import Corrida
from app.db.session import db_session
from app.alerts.connector_health import registrar_fallo
from app.connectors.adzuna import AdzunaConnector
from app.connectors.arbeitnow import ArbeitnowConnector
from app.connectors.ashby import AshbyConnector
from app.connectors.greenhouse import GreenhouseConnector
from app.connectors.himalayas import HimalayasConnector
from app.connectors.jobicy import JobicyConnector
from app.connectors.lever import LeverConnector
from app.connectors.remoteok import RemoteOKConnector
from app.connectors.remotive import RemotiveConnector

logger = logging.getLogger(__name__)

# Único lugar del proyecto donde se lista qué conectores corren en cada
# corrida (DRY: no se repite esta lista en tests ni en el scheduler).
CONECTORES_REGISTRADOS = [
    RemotiveConnector(),
    RemoteOKConnector(),
    ArbeitnowConnector(),
    JobicyConnector(),
    HimalayasConnector(),
    AdzunaConnector(),
    GreenhouseConnector(),
    LeverConnector(),
    AshbyConnector(),
]

def ejecutar_corrida() -> Corrida:
    """
    Orquesta una corrida completa:
    1. Crea fila en `corridas` (estado="enCurso").
    2. Corre todos los conectores registrados (cada uno independiente).
    3. Actualiza la fila `corridas` con `fin`, `estado`, y listas de fuentes ok/error.

    Cada conector que falla queda aislado — no tumba a los demás, solo se
    registra en `fuentes_error` y se alerta vía app.alerts.connector_health.

    Returns:
        Corrida: La fila actualizada con el resultado de la corrida.
    """
    with db_session() as db:
        logger.info("Iniciando corrida de scraping")

        # 1. Crear registro de corrida
        corrida = Corrida(estado="enCurso", fuentes_ok=[], fuentes_error=[])
        db.add(corrida)
        db.commit()
        db.refresh(corrida)

        fuentes_ok = []
        fuentes_error = []

        # 2. Ejecutar cada conector — cada uno guarda sus propios items en
        # ofertas_raw internamente (ver BaseConnector.run()), acá solo se
        # registra éxito/fallo a nivel de fuente.
        for conector in CONECTORES_REGISTRADOS:
            fuente = conector.fuente
            try:
                logger.info(f"Ejecutando conector: {fuente}")
                resultado = conector.run(db, corrida.id)

                fuentes_ok.append(fuente)
                logger.info(
                    f"Conector {fuente}: OK "
                    f"({resultado['ok']} guardadas, {resultado['descartados']} descartadas)"
                )
                db.commit()  # persiste lo que este conector guardó en ofertas_raw

            except Exception as e:
                db.rollback()  # descarta cambios parciales de ESTE conector, no de la corrida
                fuentes_error.append(fuente)
                logger.error(f"Conector {fuente} falló: {str(e)}")
                registrar_fallo(fuente=fuente, error=e, corrida_id=corrida.id)

        # 3. Actualizar corrida con resultado
        corrida.fin = datetime.utcnow()
        corrida.fuentes_ok = fuentes_ok
        corrida.fuentes_error = fuentes_error

        if fuentes_error:
            corrida.estado = "parcial" if fuentes_ok else "error"
        else:
            corrida.estado = "ok"

        db.commit()
        db.refresh(corrida)

        logger.info(
            f"Corrida #{corrida.id} completada: "
            f"estado={corrida.estado}, ok={len(fuentes_ok)}, error={len(fuentes_error)}"
        )

        return corrida
