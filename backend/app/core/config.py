import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://interviewer:interviewer_password@localhost:5432/ai_interviewer"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"
    AI_PROVIDER: str = "auto"
    ENABLE_FREE_FALLBACK: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    MAX_RESUME_SIZE_MB: int = 10
    OPENAI_TEXT_MODEL: str = "gpt-4o-mini"
    OPENAI_REALTIME_MODEL: str = "gpt-4o-realtime-preview-2024-12-17"
    OPENAI_VOICE: str = "alloy"
    HR_NOTIFICATION_EMAIL: str = "benedictrejones3101@gmail.com"
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = "AI Voice Interviewer <onboarding@resend.dev>"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@aiinterviewer.com"

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

