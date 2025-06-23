"""Configuration management for the FastAPI indexing server."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_timeout: int = 60

    # Indexing Configuration
    chunk_size: int = 512
    chunk_overlap: int = 100
    batch_size: int = 50
    default_collection_name: str = "documents_index"

    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_extensions: List[str] = [".txt", ".md", ".pdf"]
    upload_directory: str = "uploads"
    
    # API Configuration
    api_title: str = "Document Indexing API"
    api_description: str = "FastAPI server for indexing documents into Qdrant vector database"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def validate_openai_key() -> bool:
    """Validate that OpenAI API key is configured."""
    return bool(settings.openai_api_key and settings.openai_api_key.startswith("sk-"))
