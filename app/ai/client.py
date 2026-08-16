"""
TODO (Fase 2): cliente de Ollama. Única puerta de salida hacia el LLM.

Qué implementar acá:
- `class OllamaClient` con:
    - `generar(self, prompt: str, formato_json: bool = True) -> str`: llamada
      a `POST {OLLAMA_HOST}/api/generate` (o `/api/chat`), devuelve el texto
      crudo de la respuesta. **No parsea nada** — eso es de `schemas.py`.
    - `embeddings(self, texto: str) -> list[float]`: llamada a
      `POST {OLLAMA_HOST}/api/embeddings`, para el dedup semántico
      (ver `embeddings.py`).
    - `esta_disponible(self) -> bool`: ping liviano a `/api/tags` para el
      healthcheck del smoke test de CI (`docs/design.md` §4, Transversal).
- Reintentos con backoff ante error de red/timeout, igual patrón que
  `app/connectors/base.py` (mirar ese archivo antes de escribir: si la lógica
  de reintentos termina siendo idéntica, extraerla a un helper compartido en
  vez de copiarla).
- Timeout **generoso**: la latencia está aceptada por diseño
  (`requirements.md` §5.2), un 7B en una 1660 Super puede tardar decenas de
  segundos por oferta. No poner el `timeout=15` de los conectores HTTP.
- Usar `format: "json"` de Ollama cuando `formato_json=True` — fuerza al
  modelo a emitir JSON y reduce mucho el Riesgo #1.

Config nueva que hay que agregar a `app/config.py` (y a los dos `.env.example`):
    OLLAMA_HOST=http://localhost:11434   (en Docker: http://ollama:11434)
    OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
    OLLAMA_MODELO_EMBEDDINGS=nomic-embed-text
    OLLAMA_TIMEOUT_SEGUNDOS=120

DRY: ningún otro módulo hace HTTP contra Ollama. Todos importan este cliente.
"""
