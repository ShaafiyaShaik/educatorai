"""
Core configuration settings for the Educator AI Assistant
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Educator AI Administrative Assistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8003

    # Redis (optional for background tasks)
    REDIS_URL: str = "redis://localhost:6379/0"
    # Conversation state backend: 'redis' or 'memory' (default 'auto' uses redis if REDIS_URL set)
    CONVERSATION_STATE_BACKEND: str = "auto"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/educator_assistant.log"

    # Database (PostgreSQL-only)
    # Determine DATABASE_URL with this priority:
    # 1. Environment variable `DATABASE_URL` (set by the host)
    # 2. Environment variable `PRODUCTION_DATABASE_URL` (alternate key)
    # 3. A repository file `DEPLOY_DATABASE_URL` (optional, contains the URL)
    _deploy_file = Path(__file__).resolve().parents[2] / "DEPLOY_DATABASE_URL"
    _deploy_file_url = None
    if _deploy_file.exists():
        try:
            _deploy_file_url = _deploy_file.read_text(encoding="utf-8").strip()
        except Exception:
            _deploy_file_url = None

    DATABASE_URL: str = (
        os.getenv("DATABASE_URL")
        or os.getenv("PRODUCTION_DATABASE_URL")
        or _deploy_file_url
        or ""
    )

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyBWqTxhCsIWUhzORyCDlTqeg9sS6lPfXzU")
    # Gemini model to use (changeable). Default to a faster "flash" model for snappier replies.
    GEMINI_MODEL: str = "gemini-2.0-flash"
    # Tuning params to limit response size and reduce latency
    GEMINI_MAX_TOKENS: int = 256
    GEMINI_TEMPERATURE: float = 0.2
    
    # Hugging Face AI Configuration (Local AI processing - no API key needed)
    HUGGINGFACE_MODEL: str = "microsoft/DialoGPT-medium"
    USE_LOCAL_AI: bool = False  # Disabled to avoid model loading delays
    
    # Legacy OpenAI API (Optional - leave empty to use Hugging Face)
    OPENAI_API_KEY: Optional[str] = None

    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # University system integration
    UNIVERSITY_API_BASE_URL: Optional[str] = None
    UNIVERSITY_API_KEY: Optional[str] = None

    # File storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
