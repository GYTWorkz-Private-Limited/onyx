"""Environment configuration for the File Parser application."""

import os
from typing import Optional

# Try to load environment files with fallback hierarchy
try:
    from dotenv import load_dotenv
    import os

    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Try to load .env first, then fallback to .env.example
    _ENV_FILE_PATH = os.path.join(_BASE_DIR, '.env')
    _ENV_EXAMPLE_PATH = os.path.join(_BASE_DIR, '.env.example')

    if os.path.exists(_ENV_FILE_PATH):
        load_dotenv(_ENV_FILE_PATH)
        print(f"✅ Loaded configuration from .env")
    elif os.path.exists(_ENV_EXAMPLE_PATH):
        load_dotenv(_ENV_EXAMPLE_PATH)
        print(f"✅ Loaded configuration from .env.example (fallback)")
    else:
        print(f"⚠️  No .env or .env.example file found, using system environment and defaults")

except ImportError:
    print(f"⚠️  dotenv not available, using system environment and defaults only")

# Simple, reliable defaults that work well on most systems


class Environment:
    """Environment configuration class with auto-detection."""

    # LlamaParse Configuration
    LLAMA_CLOUD_API_KEY: Optional[str] = os.getenv("LLAMA_CLOUD_API_KEY")
    OUTPUT_FORMAT: str = os.getenv("OUTPUT_FORMAT", "markdown")  # markdown or text
    PARSER_MODE: str = os.getenv("PARSER_MODE", "balanced")  # fast | accurate | balanced

    # Application Configuration - Use absolute paths relative to this file
    _BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", os.path.join(_BASE_DIR, "output"))
    TEMP_DIR: str = os.getenv("TEMP_DIR", os.path.join(_BASE_DIR, "temp"))

    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # File Processing Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50000000"))  # 50MB default
    SUPPORTED_EXTENSIONS: tuple = ('.pdf', '.docx', '.csv', '.xls', '.xlsx', '.pptx')

    # Performance Configuration (CPU-optimized defaults - revised based on testing)
    ENABLE_GPU_ACCELERATION: bool = os.getenv("ENABLE_GPU_ACCELERATION", "False").lower() == "true"
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "6"))  # Revised: 6 workers for better parallelism (was 4)
    OCR_BATCH_SIZE: int = int(os.getenv("OCR_BATCH_SIZE", "6"))  # Revised: 6 batch size for better CPU utilization (was 4)
    IMAGE_SCALE: float = float(os.getenv("IMAGE_SCALE", "0.8"))  # Preserved: optimal quality vs speed balance
    MEMORY_LIMIT_MB: int = int(os.getenv("MEMORY_LIMIT_MB", "4096"))  # Optimized: increased from 1024 to reduce GC overhead


    @classmethod
    def validate_llama_config(cls) -> bool:
        """Validate LlamaParse configuration."""
        return cls.LLAMA_CLOUD_API_KEY is not None

    @classmethod
    def get_output_dir(cls) -> str:
        """Get output directory path."""
        return cls.OUTPUT_DIR

    @classmethod
    def get_temp_dir(cls) -> str:
        """Get temporary directory path."""
        return cls.TEMP_DIR


# Create directories if they don't exist
os.makedirs(Environment.OUTPUT_DIR, exist_ok=True)
os.makedirs(Environment.TEMP_DIR, exist_ok=True)
