"""Application configuration for SentimentStream."""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Settings:
    """Application settings loaded from environment variables."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "sentimentstream-dev-key")
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'sentimentstream.db')}",
    )
    PORT: int = int(os.environ.get("PORT", 8009))
    DEBUG: bool = os.environ.get("DEBUG", "0") == "1"
    TESTING: bool = False

    # Stream simulator settings
    STREAM_INTERVAL: float = float(os.environ.get("STREAM_INTERVAL", "2.0"))
    STREAM_BATCH_SIZE: int = int(os.environ.get("STREAM_BATCH_SIZE", "5"))

    # Sentiment thresholds
    POSITIVE_THRESHOLD: float = 0.2
    NEGATIVE_THRESHOLD: float = -0.2

    # Trend detection
    TREND_WINDOW_SIZE: int = 20
    SPIKE_MULTIPLIER: float = 1.5


class TestSettings(Settings):
    """Testing configuration -- uses in-memory SQLite."""

    TESTING: bool = True
    DATABASE_URL: str = "sqlite:///:memory:"
    SECRET_KEY: str = "test-secret-key"


settings = Settings()
