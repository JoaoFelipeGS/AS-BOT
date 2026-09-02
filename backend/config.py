import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # --- Configurações Gerais ---
    app_name: str = "AS Marketplace Bot SaaS"
    environment: str = "production"
    debug: bool = False
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")

    # --- produção / SaaS ---
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    allowed_origins: list[str] = [
        item.strip()
        for item in os.getenv(
            "ALLOW_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,https://localhost,https://*.vercel.app",
        ).split(",")
        if item.strip()
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    # --- Banco de Dados ---
    database_url: str = "sqlite:///./data/onora-imob.db"

    # --- SITES (Essenciais para o Extractor) ---
    base_url: str = "https://www.asimobiliaria.com"
    facebook_marketplace_create: str = "https://www.facebook.com/marketplace/create/item"
    facebook_home: str = "https://www.facebook.com"

    # --- Browser ---
    persistent_profile: str = "perfil_playwright"
    browser_slow_mo: int = 300
    browser_headless: bool = False
    view_mode: str = "visible"
    viewport_width: int = 1400
    viewport_height: int = 900

    # --- Delays Humanos (em segundos) ---
    delay_min: float = 1.5
    delay_max: float = 4.0
    delay_digitacao_min: int = 50  # ms
    delay_digitacao_max: int = 150  # ms

    # --- Integração IA ---
    gemini_api_key: str = ""
    gemini_api_url: str = ""

    # --- Credenciais/segurança do dashboard ---
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # --- Pastas (Compatibilidade total) ---
    dir_logs: str = "logs"
    dir_data: str = "data"
    logs_dir: str = "logs"
    uploads_dir: str = "images"
    screenshots_dir: str = "screenshots"
    cache_dir: str = "data"

    # --- Limites e Timeouts ---
    titulo_min: int = 5
    titulo_max: int = 90
    preco_min: int = 1000
    descricao_min: int = 50
    timeout_carregamento: int = 120000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Garante que todas as pastas existam
pastas = [
    settings.dir_logs,
    settings.dir_data,
    settings.logs_dir,
    settings.uploads_dir,
    settings.screenshots_dir,
    settings.cache_dir,
    settings.persistent_profile,
]
for pasta in pastas:
    Path(pasta).mkdir(parents=True, exist_ok=True)
