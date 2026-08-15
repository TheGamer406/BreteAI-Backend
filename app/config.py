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

    # Adzuna (gratis, 1k llamadas/mes)
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None

    # ATS — board tokens/slugs separados por coma, parsear a listas
    greenhouse_board_tokens: str = ""  # ej: "token1,token2"
    lever_companies: str = ""          # ej: "company1,company2"
    ashby_board_names: str = ""        # ej: "board1,board2"

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
