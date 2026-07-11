from pathlib import Path

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ArenaMind AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "arenamind"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MongoDB
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "arenamind"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "stadium_knowledge"
    EMBEDDING_DIM: int = 768
    EMBEDDING_MODEL: str = "nomic-ai/nomic-embed-text-v1.5"
    EMBEDDING_DEVICE: str = "cpu"

    # Kafka/Redpanda
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # LLM
    DEFAULT_LLM_PROVIDER: str = "anthropic"
    DEFAULT_LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Knowledge Base
    @property
    def KNOWLEDGE_BASE_PATH(self) -> str:
        """Auto-detect: inside Docker first, else knowledge_base/ at project root."""
        import os as _os
        if _os.path.exists("/app/knowledge_base"):
            return "/app/knowledge_base"
        # Config is at backend/app/core/config.py → project root is 4 parents up
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        return str(project_root / "knowledge_base")
        return str(project_root / "knowledge_base")

    # Stadium
    STADIUM_ID: str = "fifa_wc_2026_stadium_1"
    STADIUM_NAME: str = "FIFA World Cup 2026 Stadium"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()