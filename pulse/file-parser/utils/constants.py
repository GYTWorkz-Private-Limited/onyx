"""Constants for the File Parser application."""

# Supported file extensions
SUPPORTED_EXTENSIONS = ('.pdf', '.docx', '.csv', '.xls', '.xlsx', '.pptx')

# Default directories
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_TEMP_DIR = "temp"

# Parser engines
PARSER_ENGINES = {
    "DOCLING": "docling",
    "LLAMA": "llama"
}

# LlamaParse modes
LLAMA_PARSE_MODES = {
    "FAST": "fast",
    "ACCURATE": "accurate", 
    "BALANCED": "balanced"
}

# Output formats
OUTPUT_FORMATS = {
    "MARKDOWN": "markdown",
    "TEXT": "text"
}

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Preview text length
PREVIEW_LENGTH = 300
