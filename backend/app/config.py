"""
Application configuration.

All settings are configurable via environment variables prefixed with RECOVERAI_.
Policy thresholds are centralized here so business rules never contain magic numbers.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./recoverai.db"

    # LLM
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    ai_batch_limit: int = 50  # Max LLM calls per batch run (0 = unlimited)
    gemini_rate_limit_delay: float = 2.0  # Minimum seconds between Gemini API calls
    gemini_max_retries: int = 2  # Max retries on 429 rate limits before fallback

    # Policy thresholds (amounts in paise: 100 paise = 1 INR)
    max_retries: int = 3
    high_value_threshold: int = 5_000_000       # ₹50,000
    confidence_threshold: float = 0.6
    customer_failure_limit: int = 5
    max_auto_recovery_amount: int = 10_000_000   # ₹1,00,000
    non_retryable_reasons: list[str] = [
        "card_expired",
        "account_closed",
        "fraud_suspected",
    ]

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    model_config = {
        "env_file": (".env", "../.env"),
        "env_prefix": "RECOVERAI_",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
