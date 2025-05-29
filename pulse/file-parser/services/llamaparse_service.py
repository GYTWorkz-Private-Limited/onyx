"""LlamaParse parsing service."""

from typing import Tuple
import nest_asyncio

# Try to import from the newer llama-parse package first, fallback to llama-cloud-services
try:
    from llama_parse import LlamaParse
except ImportError:
    try:
        from llama_cloud_services import LlamaParse
    except ImportError:
        raise ImportError("Neither llama-parse nor llama-cloud-services is available")

from .base_parser import BaseParser
from models.parse_models import ParserConfig
from environment import Environment

# Ensure nest_asyncio is applied for LlamaParse
nest_asyncio.apply()


class LlamaParseService(BaseParser):
    """LlamaParse-based file parsing service."""

    def __init__(self, config: ParserConfig = None):
        """Initialize LlamaParse service."""
        if config is None:
            config = ParserConfig(
                engine="llama",
                output_format=Environment.OUTPUT_FORMAT,
                mode=Environment.PARSER_MODE
            )
        super().__init__(config)
        self._parser = None

    @property
    def parser(self) -> LlamaParse:
        """Get or create LlamaParse instance."""
        if self._parser is None:
            self._parser = self._create_parser()
        return self._parser

    def _create_parser(self) -> LlamaParse:
        """Create LlamaParse instance with configuration."""
        if not Environment.validate_llama_config():
            raise ValueError("LlamaParse API key not set in environment")

        # Create parser with minimal configuration to avoid validation issues
        try:
            return LlamaParse(
                api_key=Environment.LLAMA_CLOUD_API_KEY,
                verbose=self.config.verbose,
                num_workers=self.config.num_workers,
                language=self.config.language,
                result_type="markdown",  # Use result_type instead of output_format
            )
        except TypeError:
            # Fallback for older API
            return LlamaParse(
                api_key=Environment.LLAMA_CLOUD_API_KEY,
                verbose=self.config.verbose,
                num_workers=self.config.num_workers,
                language=self.config.language,
                output_format=self.config.output_format,
                mode=self.config.mode,
            )

    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported by LlamaParse."""
        # LlamaParse supports most common document formats
        # We'll rely on the general file validation
        return True

    def parse(self, file_path: str) -> Tuple[str, str]:
        """
        Parse file using LlamaParse.

        Args:
            file_path: Path to the file to parse

        Returns:
            Tuple[str, str]: (text_content, markdown_content)

        Raises:
            RuntimeError: If parsing fails
            ValueError: If API key is not configured
        """
        # Apply nest_asyncio before each parse operation to ensure it's active
        nest_asyncio.apply()

        try:
            # Use the load_data method which works reliably
            documents = self.parser.load_data(file_path)

            if not documents or len(documents) == 0:
                raise RuntimeError("LlamaParse returned no documents")

            # Extract text from documents
            text_parts = []
            for doc in documents:
                if hasattr(doc, 'text'):
                    text_parts.append(doc.text)
                elif hasattr(doc, 'get_content'):
                    text_parts.append(doc.get_content())
                else:
                    text_parts.append(str(doc))

            text = "\n\n".join(text_parts)
            markdown = text  # LlamaParse already returns markdown format

            return text, markdown

        except Exception as e:
            raise RuntimeError(f"LlamaParse failed: {str(e)}")

    def validate_configuration(self) -> bool:
        """Validate LlamaParse configuration."""
        return Environment.validate_llama_config()

    def get_parser_info(self) -> dict:
        """Get information about the parser configuration."""
        return {
            "engine": self.config.engine,
            "output_format": self.config.output_format,
            "mode": self.config.mode,
            "language": self.config.language,
            "num_workers": self.config.num_workers,
            "api_key_configured": Environment.validate_llama_config()
        }
