import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management for PostgreSQL database connection.

    This class handles loading and validating environment variables
    for database connection and connection pool settings.
    """

    # Database connection settings
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USE_SSL: bool = False
    POSTGRES_SSL_MODE: Optional[str] = None
    POSTGRES_SSL_ROOT_CERT: Optional[str] = None

    # Connection pool settings
    POSTGRES_POOL_SIZE: int = 5
    POSTGRES_MAX_OVERFLOW: int = 10
    POSTGRES_POOL_TIMEOUT: int = 30
    POSTGRES_POOL_RECYCLE: int = 3600
    POSTGRES_POOL_PRE_PING: bool = True
    POSTGRES_ECHO_SQL: bool = False

    @classmethod
    def validate(cls):
        """Load and validate environment variables"""
        # Required variables
        required_vars = {
            'POSTGRES_HOST': os.getenv("POSTGRES_HOST"),
            'POSTGRES_USER': os.getenv("POSTGRES_USER"),
            'POSTGRES_PASSWORD': os.getenv("POSTGRES_PASSWORD"),
            'POSTGRES_DB': os.getenv("POSTGRES_DB")
        }

        # Set values and check for missing variables
        missing = []
        for key, value in required_vars.items():
            setattr(cls, key, value)
            if value is None:
                missing.append(key)

        if missing:
            raise ValueError(f"Missing required config variables: {', '.join(missing)}")

        # Optional variables with defaults
        cls.POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
        cls.POSTGRES_USE_SSL = os.getenv("POSTGRES_USE_SSL", "false").lower() == "true"
        cls.POSTGRES_SSL_MODE = os.getenv("POSTGRES_SSL_MODE", "verify-ca" if cls.POSTGRES_USE_SSL else None)
        cls.POSTGRES_SSL_ROOT_CERT = os.getenv("POSTGRES_SSL_ROOT_CERT")

        # Connection Pool settings - configurable via environment variables
        cls.POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", 5))
        cls.POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", 10))
        cls.POSTGRES_POOL_TIMEOUT = int(os.getenv("POSTGRES_POOL_TIMEOUT", 30))
        cls.POSTGRES_POOL_RECYCLE = int(os.getenv("POSTGRES_POOL_RECYCLE", 3600))
        cls.POSTGRES_POOL_PRE_PING = os.getenv("POSTGRES_POOL_PRE_PING", "true").lower() == "true"
        cls.POSTGRES_ECHO_SQL = os.getenv("POSTGRES_ECHO_SQL", "false").lower() == "true"
