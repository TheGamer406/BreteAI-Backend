"""
Worker que consume la cola: `ofertas_raw` pendiente -> IA -> `ofertas`.
Etapa 2 del pipeline (docs/design.md §1).
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.ai.analyzer import analizar_oferta
from app.ai.client import OllamaClient
from app.ai.embeddings import buscar_similar, calcular_embedding
from app.ai.perfil import Perfil, cargar_perfil
from app.ai.salario import estimar_salario
from app.connectors.registro import REGISTRO_CONECTORES
from app.db.models import Oferta, OfertaRaw
from app.feedback.criterios import derivar_criterios

logger = logging.getLogger(__name__)

MAX_INTENTOS_RAW = 3


def procesar_pendientes(db: Session, limite: Optional[int] = None) -> dict:
    """
    Procesa las filas `ofertas_raw` con `estado_proc='pendiente'`: re-mapea
    el payload crudo a canónico, analiza con IA, guarda en `ofertas`.

    Commit por fila (no por lote completo): si el proceso se cae a la mitad,
    lo ya analizado no se pierde. Fallos aislados -- una raw que falla no
    tumba las demás, queda en `error` con `error_msg` e `intentos += 1`.

    Returns:
        {"procesadas": int, "errores": int}
    """
    perfil = cargar_perfil()
    # Se deriva una sola vez por corrida del worker (query a feedback_ia),
    # no una vez por oferta -- son cientos de ofertas por corrida.
    criterios_extra = derivar_criterios(db)

    query = db.query(OfertaRaw).filter(OfertaRaw.estado_proc == "pendiente")
    if limite:
        query = query.limit(limite)
    pendientes = query.all()

    procesadas = 0
    errores = 0

    for raw in pendientes:
        try:
            _procesar_una(db, raw, perfil, criterios_extra)
            db.commit()
            procesadas += 1
        except Exception as e:
            db.rollback()
            # Tras el rollback la sesión expira los objetos -- re-obtener
            # la raw en la transacción nueva antes de marcarla error.
            raw_fresca = db.get(OfertaRaw, raw.id)
            raw_fresca.estado_proc = "error"
            raw_fresca.error_msg = str(e)[:2000]
            raw_fresca.intentos += 1
            db.commit()
            errores += 1
            logger.warning(f"[worker] raw #{raw.id} ({raw.fuente}) falló: {e}")

    logger.info(f"[worker] {procesadas} procesadas, {errores} errores")
    return {"procesadas": procesadas, "errores": errores}


def _procesar_una(
    db: Session, raw: OfertaRaw, perfil: Perfil, criterios_extra: list[str]
) -> None:
    conector_cls = REGISTRO_CONECTORES.get(raw.fuente)
    if conector_cls is None:
        raise ValueError(f"Fuente desconocida: {raw.fuente} (raw #{raw.id})")

    # payload = JSON crudo original (design.md §1) -- se re-mapea acá con
    # el _map() del conector correspondiente, NO se guardó el canónico.
    conector = conector_cls()
    oferta_canonica = conector._map(raw.payload)
    if oferta_canonica is None:
        raise ValueError(f"El payload de raw #{raw.id} ya no es mapeable")

    existente = (
        db.query(Oferta)
        .filter(
            Oferta.fuente == oferta_canonica.fuente,
            Oferta.id_externo == oferta_canonica.id_externo,
        )
        .first()
    )
    if existente is not None:
        # Ya procesada antes (ej. re-vista en otra corrida): no reanalizar
        # -- ahorra GPU. Solo se asegura que la raw quede consistente.
        raw.estado_proc = "procesada"
        return

    analisis = analizar_oferta(oferta_canonica, perfil, criterios_extra)

    salario_min = oferta_canonica.salario_min
    salario_max = oferta_canonica.salario_max
    salario_moneda = oferta_canonica.salario_moneda
    salario_estimado = False
    if salario_min is None and salario_max is None:
        salario_min, salario_max, salario_moneda = estimar_salario(db, oferta_canonica)
        salario_estimado = salario_min is not None or salario_max is not None

    client = OllamaClient()
    embedding = calcular_embedding(oferta_canonica, client=client)
    similar_a = buscar_similar(db, oferta_canonica, embedding)

    oferta = Oferta(
        raw_id=raw.id,
        fuente=oferta_canonica.fuente,
        id_externo=oferta_canonica.id_externo,
        titulo=oferta_canonica.titulo,
        empresa=oferta_canonica.empresa,
        ubicacion=oferta_canonica.ubicacion,
        pais=oferta_canonica.pais,
        modalidad=oferta_canonica.modalidad.value if oferta_canonica.modalidad else None,
        salario_min=salario_min,
        salario_max=salario_max,
        salario_moneda=salario_moneda,
        salario_estimado=salario_estimado,
        descripcion=oferta_canonica.descripcion,
        url=oferta_canonica.url,
        fecha_publicacion=oferta_canonica.fecha_publicacion,
        resumen=analisis.resumen,
        requisitos=analisis.requisitos,
        beneficios=analisis.beneficios,
        seniority=analisis.seniority,
        empresa_real=analisis.empresa_real,
        score=analisis.score,
        score_razon=analisis.score_razon,
        embedding=embedding,
        similar_a=similar_a,
    )
    db.add(oferta)
    raw.estado_proc = "procesada"


def reprocesar_errores(db: Session, max_intentos: int = MAX_INTENTOS_RAW) -> int:
    """Vuelve a poner en 'pendiente' las raws en 'error' que no superaron
    `max_intentos`. No las procesa acá -- solo las re-encola; la próxima
    llamada a `procesar_pendientes()` las toma."""
    raws = (
        db.query(OfertaRaw)
        .filter(OfertaRaw.estado_proc == "error", OfertaRaw.intentos < max_intentos)
        .all()
    )
    for raw in raws:
        raw.estado_proc = "pendiente"
    db.commit()
    return len(raws)
