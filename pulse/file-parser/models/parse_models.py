"""Data models for parse operations."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class ParseResult:
    """Result of a file parsing operation."""
    text: str
    markdown: str
    filename: str
    engine: str
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def get_text_preview(self, length: int = 300) -> str:
        """Get a preview of the text content."""
        return self.text[:length] if self.text else ""
    
    def get_markdown_preview(self, length: int = 300) -> str:
        """Get a preview of the markdown content."""
        return self.markdown[:length] if self.markdown else ""
    
    def get_file_stem(self) -> str:
        """Get filename without extension."""
        return Path(self.filename).stem


@dataclass
class ParserConfig:
    """Configuration for parser operations."""
    engine: str
    output_format: str = "markdown"
    mode: str = "balanced"
    language: str = "en"
    num_workers: int = 4
    verbose: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine": self.engine,
            "output_format": self.output_format,
            "mode": self.mode,
            "language": self.language,
            "num_workers": self.num_workers,
            "verbose": self.verbose
        }


@dataclass
class FileMetadata:
    """Metadata about a processed file."""
    filename: str
    size: Optional[int] = None
    extension: Optional[str] = None
    content_type: Optional[str] = None
    processing_time: Optional[float] = None
    
    def __post_init__(self):
        """Set extension from filename if not provided."""
        if not self.extension and self.filename:
            self.extension = Path(self.filename).suffix.lower()
