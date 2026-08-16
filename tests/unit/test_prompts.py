"""
TODO (Fase 2): armado del prompt. Sin red, sin GPU — son strings puros.

Casos a cubrir:
- El prompt incluye los datos clave del perfil (seniority, intereses_rol,
  keywords, criterios de penalizar/bonificar). Usar un `Perfil` de prueba
  construido a mano — **NO leer `resources/perfil.toon`** (datos personales
  reales; los tests no deben depender de él ni exponerlo).
- El prompt incluye los datos de la oferta (titulo, empresa, descripcion).
- Descripción muy larga (ej: 50k caracteres de HTML de Greenhouse) → el
  prompt queda truncado al límite definido, no crece sin control.
- La descripción en HTML llega limpia al prompt (sin tags).
- `criterios_extra` (feedback del usuario) aparecen en el prompt cuando se
  pasan, y el prompt funciona igual cuando son `None`.
- El prompt pide explícitamente JSON y resumen en español.

Este test es la red de seguridad para tocar el prompt sin miedo: si alguien
"mejora" el prompt y se olvida de incluir los criterios de match, acá salta.
"""
