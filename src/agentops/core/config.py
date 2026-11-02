from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://agentops:agentops@localhost:5432/agentops"
    agentops_api_key: SecretStr = SecretStr("local-development-only")
    cors_origins: str = "http://localhost:8501"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def reject_insecure_production_key(self):
        if self.app_env.lower() == "production":
            if len(self.agentops_api_key.get_secret_value()) < 32:
                raise ValueError(
                    "AGENTOPS_API_KEY must contain at least 32 characters in production"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
