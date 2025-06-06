"""Abstract base parser class."""

from abc import ABC, abstractmethod
from typing import Tuple
from models.parse_models import ParseResult, ParserConfig


class BaseParser(ABC):
    """Abstract base class for file parsers."""
    
    def __init__(self, config: ParserConfig):
        """Initialize parser with configuration."""
        self.config = config
    
    @abstractmethod
    def parse(self, file_path: str) -> Tuple[str, str]:
        """
        Parse a file and return text and markdown content.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Tuple[str, str]: (text_content, markdown_content)
            
        Raises:
            RuntimeError: If parsing fails
            ValueError: If file format is not supported
        """
        pass
    
    @abstractmethod
    def is_supported(self, file_path: str) -> bool:
        """
        Check if the file format is supported by this parser.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        pass
    
    def parse_to_result(self, file_path: str, filename: str) -> ParseResult:
        """
        Parse file and return a ParseResult object.
        
        Args:
            file_path: Path to the file to parse
            filename: Original filename
            
        Returns:
            ParseResult: Result object with parsed content
        """
        try:
            text, markdown = self.parse(file_path)
            return ParseResult(
                text=text,
                markdown=markdown,
                filename=filename,
                engine=self.config.engine,
                success=True
            )
        except Exception as e:
            return ParseResult(
                text="",
                markdown="",
                filename=filename,
                engine=self.config.engine,
                success=False,
                error_message=str(e)
            )
    
    def get_engine_name(self) -> str:
        """Get the name of this parser engine."""
        return self.config.engine
