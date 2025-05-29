"""Environment configuration for the File Parser application."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Environment:
    """Environment configuration class."""
    
    # LlamaParse Configuration
    LLAMA_CLOUD_API_KEY: Optional[str] = os.getenv("LLAMA_CLOUD_API_KEY")
    OUTPUT_FORMAT: str = os.getenv("OUTPUT_FORMAT", "markdown")  # markdown or text
    PARSER_MODE: str = os.getenv("PARSER_MODE", "balanced")  # fast | accurate | balanced
    
    # Application Configuration
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")
    
    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # File Processing Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50000000"))  # 50MB default
    SUPPORTED_EXTENSIONS: tuple = ('.pdf', '.docx', '.csv', '.xls', '.xlsx', '.pptx')
    
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
