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

## Desarrollo

_Pendiente: instrucciones de setup (venv, dependencias, variables de entorno)._

```bash
cp .env.example .env   # configurar credenciales
```
