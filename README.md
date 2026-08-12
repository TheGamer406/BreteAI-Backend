# BreteAI-Backend

Backend de [BreteAI](https://github.com/TheGamer406/BreteAI) — scraping de ofertas, pipeline de IA local y API REST.

## Responsabilidades

- Conectores a fuentes legales de empleo (APIs oficiales + ATS).
- Scheduler (4 corridas/día: 05:00, 11:00, 16:00, 22:00 CR).
- Pipeline de IA con Ollama: resumen, extracción de campos, score de match, dedup semántico.
- API REST para el frontend (con autenticación).
- Envío de correos (Gmail SMTP).

## Stack

Python · FastAPI · Ollama · SQLAlchemy/psycopg (PostgreSQL) · APScheduler.

## Implementación

**Antes de escribir código acá**, leer `docs/GUIA-IMPLEMENTACION.md` (en el repo padre) —
es el índice por fase con el orden exacto de archivos a completar. El esqueleto de
`app/` y `tests/` ya existe: cada archivo tiene un docstring con el detalle de qué
implementar y qué no duplicar.

## Desarrollo

_Pendiente: instrucciones de setup (venv, dependencias, variables de entorno)._

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # configurar credenciales (pendiente crear .env.example)
```
