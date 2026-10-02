import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://interviewer:interviewer_password@localhost:5432/ai_interviewer"
    OPENAI_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    MAX_RESUME_SIZE_MB: int = 10
    OPENAI_TEXT_MODEL: str = "gpt-4o-mini"
    OPENAI_REALTIME_MODEL: str = "gpt-4o-realtime-preview-2024-12-17"
    OPENAI_VOICE: str = "alloy"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins


settings = Settings()

