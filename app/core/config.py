from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Preview Diagnostic Tool"
    app_env: str = "development"
    app_cors_origins: str = "http://localhost:3000,http://localhost:5173"

    llm_provider: str = "mock"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-12-01-preview"

    database_url: str = (
        "postgresql+asyncpg://preview_diagnostic:preview_diagnostic@localhost:5432/"
        "preview_diagnostic"
    )
    embedding_model: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]


settings = Settings()
