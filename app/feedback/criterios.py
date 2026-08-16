"""
Feedback simple del usuario -> ajustes de los criterios del prompt. NO es
re-entrenamiento (requirements.md §5.1, decisión cerrada).

Flujo: el usuario corrige en el portal (Fase 4) -> se guarda en
`feedback_ia` -> la próxima corrida arma el prompt incluyendo esas
correcciones como `criterios_extra` (ver `app/ai/prompts.py`).
"""

import logging
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import FeedbackIA

logger = logging.getLogger(__name__)

# Tope de criterios inyectados al prompt -- sin límite, el prompt crece sin
# control y desborda el contexto del modelo, degradando todo lo demás.
LIMITE_CRITERIOS_DEFAULT = 20


def registrar_correccion(
    db: Session,
    oferta_id: int,
    campo: str,
    valor_ia: Optional[str],
    valor_correcto: str,
    nota: Optional[str] = None,
) -> FeedbackIA:
    """Guarda una corrección del usuario. La llamará un endpoint del portal
    en Fase 4; por ahora sirve para sembrar datos a mano/en tests."""
    feedback = FeedbackIA(
        oferta_id=oferta_id,
        campo=campo,
        valor_ia=valor_ia,
        valor_correcto=valor_correcto,
        nota=nota,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def derivar_criterios(db: Session, limite: int = LIMITE_CRITERIOS_DEFAULT) -> list[str]:
    """
    Lee las correcciones más recientes y las convierte en líneas de texto
    para `criterios_extra` del prompt. Agrupa correcciones repetidas del
    mismo campo en un solo criterio en vez de repetir N líneas casi iguales.
    """
    correcciones = (
        db.query(FeedbackIA).order_by(FeedbackIA.creado_en.desc()).limit(200).all()
    )
    if not correcciones:
        return []

    por_campo: dict[str, list[FeedbackIA]] = {}
    for c in correcciones:
        por_campo.setdefault(c.campo, []).append(c)

    criterios: list[tuple[int, str]] = []  # (frecuencia, texto) para priorizar

    for campo, items in por_campo.items():
        if len(items) == 1:
            c = items[0]
            texto = f"Corrección en '{campo}': la IA dijo '{c.valor_ia}', el valor correcto era '{c.valor_correcto}'"
            if c.nota:
                texto += f" ({c.nota})"
            criterios.append((1, texto))
        else:
            # Correcciones repetidas del mismo campo: un solo criterio
            # agregado con las notas más frecuentes, no N líneas casi iguales.
            notas = [c.nota for c in items if c.nota]
            nota_comun = Counter(notas).most_common(1)[0][0] if notas else None
            texto = f"Corrección recurrente en '{campo}' ({len(items)} veces)"
            if nota_comun:
                texto += f": {nota_comun}"
            criterios.append((len(items), texto))

    # Priorizar por frecuencia (más repetido primero), tope de `limite`.
    criterios.sort(key=lambda x: x[0], reverse=True)
    return [texto for _, texto in criterios[:limite]]
