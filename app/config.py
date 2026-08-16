from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Configuración central del proyecto vía variables de entorno."""

    # Base de datos (ver BreteAI-Infra/.env.example)
    database_url: str

    # API — default seguro para desarrollo local (solo localhost).
    # En Docker el compose setea API_HOST=0.0.0.0 para exponer dentro de la red.
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Correo (Fase 3) — destinatario de las notificaciones. Configurable para
    # que el proyecto sirva a cualquier usuario sin datos personales en el repo.
    mail_to: Optional[str] = None

    # SMTP (Fase 3) — Gmail con App Password en producción (requirements.md
    # §10, DECISIÓN). En tests: MailHog (smtp_usa_tls=False, no habla TLS).
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None  # App Password de 16 caracteres, NUNCA la del correo
    mail_from: Optional[str] = None
    smtp_usa_tls: bool = True

    # URL base del portal (Fase 4) para los links de las cards del correo.
    portal_base_url: str = "http://localhost:3000"

    # Adzuna (gratis, 1k llamadas/mes)
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None

    # ATS — board tokens/slugs separados por coma, parsear a listas
    greenhouse_board_tokens: str = ""  # ej: "token1,token2"
    lever_companies: str = ""          # ej: "company1,company2"
    ashby_board_names: str = ""        # ej: "board1,board2"

    # IA (Fase 2) — servidor con API OpenAI-compatible (Ollama en producción;
    # LM Studio funciona igual para desarrollo local, mismo endpoint /v1/*).
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct-q4_K_M"
    ollama_modelo_embeddings: str = "nomic-embed-text"
    ollama_timeout_segundos: int = 120

    # Ruta al perfil TOON. Relativa (default): se resuelve contra la raíz
    # del repo backend asumiendo el checkout monorepo (resources/ vive un
    # nivel arriba de BreteAI-Backend/). Absoluta: para Docker/producción,
    # apuntar a donde se monte el volumen con el perfil real.
    perfil_path: str = "../resources/perfil.toon"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    def get_greenhouse_tokens(self) -> list[str]:
        """Retorna lista de board tokens de Greenhouse."""
        return [t.strip() for t in self.greenhouse_board_tokens.split(",") if t.strip()]

    def get_lever_companies(self) -> list[str]:
        """Retorna lista de slugs de Lever."""
        return [c.strip() for c in self.lever_companies.split(",") if c.strip()]

    def get_ashby_boards(self) -> list[str]:
        """Retorna lista de board names de Ashby."""
        return [b.strip() for b in self.ashby_board_names.split(",") if b.strip()]

@lru_cache
def get_settings() -> Settings:
    """Singleton cacheado de Settings — se lee .env una sola vez."""
    return Settings()
