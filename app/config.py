from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Configuración central del proyecto vía variables de entorno."""

    # Base de datos (ver BreteAI-Infra/.env.example)
    database_url: str

    # Adzuna (gratis, 1k llamadas/mes)
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None

    # ATS — board tokens/slugs separados por coma, parsear a listas
    greenhouse_board_tokens: str = ""  # ej: "token1,token2"
    lever_companies: str = ""          # ej: "company1,company2"
    ashby_board_names: str = ""        # ej: "board1,board2"

    class Config:
        env_file = ".env"
        case_sensitive = False

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
