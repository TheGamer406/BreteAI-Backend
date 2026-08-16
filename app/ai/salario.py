"""
TODO (Fase 2): estimación de salario cuando la oferta no lo publica
(`requirements.md` §4.4: "buscar referencia web; si no hay, guardar
null / 'no especificado'").

Qué implementar acá:
- `estimar_salario(oferta: OfertaCanonica) -> tuple[float|None, float|None, str|None]`:
  devuelve `(min, max, moneda)` o `(None, None, None)`.
  Solo se llama cuando la oferta NO trae salario (varias fuentes nunca lo
  traen: Remotive, Arbeitnow).

Reglas duras:
- Si no se consigue una referencia confiable → **`None`, no un número
  inventado**. Un salario alucinado por el LLM es peor que un campo vacío:
  contamina el score y las métricas del dashboard.
- Todo lo estimado se marca con `ofertas.salario_estimado = True` (la columna
  ya existe). El portal debe poder distinguir "la empresa dijo 50k" de
  "estimamos 50k" — no mezclarlos nunca en el dashboard.

Sobre "buscar referencia web": el proyecto es 100% local y sin API de pago.
Evaluar al implementar, en este orden de preferencia:
  1. Derivarlo de datos que YA tenemos: Adzuna sí publica salarios y es una
     fuente de referencia buena para rangos por rol/país
     (`requirements.md` §4.1 la menciona justo por esto). Promediar ofertas
     similares ya guardadas en `ofertas` es gratis, offline y auditable.
  2. Pedirle al LLM una estimación por rol+país (poco confiable, alto riesgo
     de alucinación; si se hace, exigir que devuelva rango y confianza, y
     descartar cuando la confianza sea baja).
  3. Scraping de sitios de salarios → NO en v1 (mismo criterio legal de
     `requirements.md` §4: solo APIs oficiales).
Arrancar por (1). Si (1) no da datos suficientes, dejar `None` — es una
respuesta válida y honesta.
"""
