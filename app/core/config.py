from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./ai_automation.db"

    codex_backend: Literal["stub", "sdk"] = "stub"
    codex_model: str | None = None
    codex_api_key: SecretStr | None = None
    codex_workspace_root: Path = Path("./workspaces")
    codex_default_workspace: str = "default"

    investment_agent_model: str | None = None
    investment_agent_max_turns: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()
