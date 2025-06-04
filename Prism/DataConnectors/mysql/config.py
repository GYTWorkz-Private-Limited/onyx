import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management for MySQL database connection.

    This class handles loading and validating environment variables
    for database connection and connection pool settings.
    """

    # Database connection settings
    MYSQL_HOST: Optional[str] = None
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_DB: Optional[str] = None
    MYSQL_PORT: int = 3306
    MYSQL_USE_SSL: bool = False
    MYSQL_SSL_CA: Optional[str] = None

    # Connection pool settings
    MYSQL_POOL_SIZE: int = 5
    MYSQL_MAX_OVERFLOW: int = 10
    MYSQL_POOL_TIMEOUT: int = 30
    MYSQL_POOL_RECYCLE: int = 3600
    MYSQL_POOL_PRE_PING: bool = True
    MYSQL_ECHO_SQL: bool = False

    @classmethod
    def validate(cls):
        """Load and validate environment variables"""
        # Required variables
        required_vars = {
            'MYSQL_HOST': os.getenv("MYSQL_HOST"),
            'MYSQL_USER': os.getenv("MYSQL_USER"),
            'MYSQL_PASSWORD': os.getenv("MYSQL_PASSWORD"),
            'MYSQL_DB': os.getenv("MYSQL_DB")
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
        cls.MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
        cls.MYSQL_USE_SSL = os.getenv("MYSQL_USE_SSL", "false").lower() == "true"
        cls.MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA")

        # Connection Pool settings
        cls.MYSQL_POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", 5))
        cls.MYSQL_MAX_OVERFLOW = int(os.getenv("MYSQL_MAX_OVERFLOW", 10))
        cls.MYSQL_POOL_TIMEOUT = int(os.getenv("MYSQL_POOL_TIMEOUT", 30))
        cls.MYSQL_POOL_RECYCLE = int(os.getenv("MYSQL_POOL_RECYCLE", 3600))
        cls.MYSQL_POOL_PRE_PING = os.getenv("MYSQL_POOL_PRE_PING", "true").lower() == "true"
        cls.MYSQL_ECHO_SQL = os.getenv("MYSQL_ECHO_SQL", "false").lower() == "true"
