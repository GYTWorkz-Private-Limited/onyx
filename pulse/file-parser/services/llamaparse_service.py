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
            raise ValueError(
                "LlamaParse API key not set in environment. "
                "Please set LLAMA_CLOUD_API_KEY in your .env file or use the Docling engine instead."
            )

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
            try:
                return LlamaParse(
                    api_key=Environment.LLAMA_CLOUD_API_KEY,
                    verbose=self.config.verbose,
                    num_workers=self.config.num_workers,
                    language=self.config.language,
                    output_format=self.config.output_format,
                    mode=self.config.mode,
                )
            except Exception as e:
                raise RuntimeError(f"Failed to create LlamaParse instance: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to create LlamaParse instance: {str(e)}")

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
            import os
            file_ext = os.path.splitext(file_path)[1].lower()

            # Additional integrity check for Office documents
            if file_ext in ['.docx', '.xlsx', '.pptx']:
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(4)
                        if header[:2] != b'PK':
                            # File might be corrupted, but let's try anyway
                            pass
                except Exception:
                    # Could not check file header, continue anyway
                    pass

            # Use the load_data method which works reliably
            documents = self.parser.load_data(file_path)

            if not documents or len(documents) == 0:
                # Try alternative parsing approaches for problematic formats
                if file_ext in ['.docx', '.pptx']:
                    # Strategy 1: Try with different result type
                    try:
                        alt_parser1 = LlamaParse(
                            api_key=Environment.LLAMA_CLOUD_API_KEY,
                            result_type="text",
                            verbose=True,
                            language="en"
                        )
                        documents = alt_parser1.load_data(file_path)
                        if not documents or len(documents) == 0:
                            raise Exception("Still no documents")
                    except Exception:

                        # Strategy 2: Try copying file to new location
                        try:
                            import shutil
                            import tempfile

                            # Create a new temporary file
                            with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
                                tmp_path = tmp_file.name

                            # Copy the original file
                            shutil.copy2(file_path, tmp_path)

                            # Try parsing the copy
                            documents = self.parser.load_data(tmp_path)

                            # Clean up
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass

                            if not documents or len(documents) == 0:
                                raise Exception("Still no documents with copy")

                        except Exception:
                            pass

                if not documents or len(documents) == 0:
                    raise RuntimeError(f"LlamaParse returned no documents for {file_ext} file after trying multiple strategies. This may be due to file format limitations, content issues, or API constraints.")

            # Extract text from documents
            text_parts = []
            for doc in documents:
                if hasattr(doc, 'text'):
                    content = doc.text
                    text_parts.append(content)
                elif hasattr(doc, 'get_content'):
                    content = doc.get_content()
                    text_parts.append(content)
                else:
                    content = str(doc)
                    text_parts.append(content)

            # Filter out empty parts
            text_parts = [part for part in text_parts if part and part.strip()]

            if not text_parts:
                raise RuntimeError(f"LlamaParse returned documents but all content was empty for {file_ext} file")

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
