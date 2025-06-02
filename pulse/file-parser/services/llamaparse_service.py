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
            # Debug information
            import os
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            print(f"DEBUG: LlamaParse processing {file_ext} file, size: {file_size} bytes")

            # Additional integrity check for Office documents
            if file_ext in ['.docx', '.xlsx', '.pptx']:
                print(f"DEBUG: Performing integrity check for {file_ext}")
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(4)
                        if header[:2] == b'PK':
                            print(f"DEBUG: Valid ZIP header found for {file_ext}")
                        else:
                            print(f"DEBUG: WARNING - Invalid header for {file_ext}: {header}")
                            # File might be corrupted, but let's try anyway
                except Exception as e:
                    print(f"DEBUG: Could not check file header: {e}")

            # Use the load_data method which works reliably
            documents = self.parser.load_data(file_path)

            print(f"DEBUG: LlamaParse returned {len(documents) if documents else 0} documents")

            if not documents or len(documents) == 0:
                # Try alternative parsing approaches for problematic formats
                if file_ext in ['.docx', '.pptx']:
                    print(f"DEBUG: Attempting alternative parsing strategies for {file_ext}")

                    # Strategy 1: Try with different result type
                    try:
                        print(f"DEBUG: Trying with text result type...")
                        alt_parser1 = LlamaParse(
                            api_key=Environment.LLAMA_CLOUD_API_KEY,
                            result_type="text",
                            verbose=True,
                            language="en"
                        )
                        documents = alt_parser1.load_data(file_path)
                        print(f"DEBUG: Text parser returned {len(documents) if documents else 0} documents")
                        if documents and len(documents) > 0:
                            print(f"DEBUG: Success with text result type!")
                        else:
                            raise Exception("Still no documents")
                    except Exception as alt_e1:
                        print(f"DEBUG: Text parsing failed: {alt_e1}")

                        # Strategy 2: Try copying file to new location
                        try:
                            print(f"DEBUG: Trying with file copy...")
                            import shutil
                            import tempfile

                            # Create a new temporary file
                            with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
                                tmp_path = tmp_file.name

                            # Copy the original file
                            shutil.copy2(file_path, tmp_path)
                            print(f"DEBUG: Copied file to {tmp_path}")

                            # Try parsing the copy
                            documents = self.parser.load_data(tmp_path)
                            print(f"DEBUG: Copy parser returned {len(documents) if documents else 0} documents")

                            # Clean up
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass

                            if documents and len(documents) > 0:
                                print(f"DEBUG: Success with file copy!")
                            else:
                                raise Exception("Still no documents with copy")

                        except Exception as alt_e2:
                            print(f"DEBUG: Copy parsing failed: {alt_e2}")

                if not documents or len(documents) == 0:
                    raise RuntimeError(f"LlamaParse returned no documents for {file_ext} file after trying multiple strategies. This may be due to file format limitations, content issues, or API constraints.")

            # Extract text from documents
            text_parts = []
            for i, doc in enumerate(documents):
                print(f"DEBUG: Processing document {i+1}/{len(documents)}")
                if hasattr(doc, 'text'):
                    content = doc.text
                    print(f"DEBUG: Document {i+1} text length: {len(content) if content else 0}")
                    text_parts.append(content)
                elif hasattr(doc, 'get_content'):
                    content = doc.get_content()
                    print(f"DEBUG: Document {i+1} content length: {len(content) if content else 0}")
                    text_parts.append(content)
                else:
                    content = str(doc)
                    print(f"DEBUG: Document {i+1} string length: {len(content) if content else 0}")
                    text_parts.append(content)

            # Filter out empty parts
            text_parts = [part for part in text_parts if part and part.strip()]

            if not text_parts:
                raise RuntimeError(f"LlamaParse returned documents but all content was empty for {file_ext} file")

            text = "\n\n".join(text_parts)
            markdown = text  # LlamaParse already returns markdown format

            print(f"DEBUG: Final text length: {len(text)}")
            return text, markdown

        except Exception as e:
            print(f"DEBUG: LlamaParse exception: {type(e).__name__}: {e}")
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
