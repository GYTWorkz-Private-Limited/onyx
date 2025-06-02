"""Parse controller for handling file parsing business logic."""

import os
from typing import Dict, Any
from fastapi import UploadFile, HTTPException

from models.parse_models import ParseResult
from services.docling_service import DoclingService
from services.llamaparse_service import LlamaParseService
from utils.file_validator import FileValidator
from utils.output_writer import OutputWriter
from schemas.parse_schemas import ParserEngine
from utils.constants import PREVIEW_LENGTH


class ParseController:
    """Controller for handling file parsing operations."""

    def __init__(self):
        """Initialize the parse controller."""
        self._docling_service = None
        self._llamaparse_service = None

    @property
    def docling_service(self) -> DoclingService:
        """Get or create Docling service instance."""
        if self._docling_service is None:
            try:
                self._docling_service = DoclingService()
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize Docling service: {str(e)}"
                )
        return self._docling_service

    @property
    def llamaparse_service(self) -> LlamaParseService:
        """Get or create LlamaParse service instance."""
        if self._llamaparse_service is None:
            try:
                self._llamaparse_service = LlamaParseService()
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize LlamaParse service: {str(e)}"
                )
        return self._llamaparse_service

    def get_parser_service(self, engine: ParserEngine):
        """Get the appropriate parser service based on engine."""
        if engine == ParserEngine.DOCLING:
            return self.docling_service
        elif engine == ParserEngine.LLAMA:
            return self.llamaparse_service
        else:
            raise ValueError(f"Unsupported parser engine: {engine}")

    async def parse_file(self, file: UploadFile, engine: ParserEngine) -> Dict[str, Any]:
        """
        Parse uploaded file using specified engine.

        Args:
            file: Uploaded file
            engine: Parser engine to use

        Returns:
            Dict[str, Any]: Parse result response

        Raises:
            HTTPException: If validation or parsing fails
        """
        # Validate file
        FileValidator.validate_and_raise(file)

        filename = file.filename
        temp_path = FileValidator.generate_temp_path(filename)

        try:
            # Save uploaded file to temporary location
            await self._save_uploaded_file(file, temp_path)

            # Verify the uploaded file
            if not os.path.exists(temp_path):
                raise RuntimeError(f"Temporary file was not created: {temp_path}")

            file_size = os.path.getsize(temp_path)
            print(f"DEBUG: Uploaded file saved to {temp_path}, size: {file_size} bytes")

            if file_size == 0:
                raise RuntimeError(f"Uploaded file is empty: {temp_path}")

            # Add a small delay to ensure file is fully written and closed
            import time
            time.sleep(0.1)

            # Verify file is readable
            try:
                with open(temp_path, 'rb') as test_file:
                    test_content = test_file.read(100)  # Read first 100 bytes
                    print(f"DEBUG: File verification - can read {len(test_content)} bytes")
            except Exception as e:
                raise RuntimeError(f"Cannot read temporary file: {e}")

            # Get parser service
            parser_service = self.get_parser_service(engine)

            # Parse the file
            print(f"DEBUG: Parsing file {temp_path} with engine {engine}")
            result = parser_service.parse_to_result(temp_path, filename)
            print(f"DEBUG: Parse result success: {result.success}")
            print(f"DEBUG: Text length: {len(result.text) if result.text else 0}")
            print(f"DEBUG: Markdown length: {len(result.markdown) if result.markdown else 0}")

            if not result.success:
                print(f"DEBUG: Parse failed with error: {result.error_message}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Parsing failed: {result.error_message}"
                )

            # Check for empty content even if parsing was "successful"
            if not result.text or not result.text.strip():
                print(f"DEBUG: Parse returned empty text content!")
                raise HTTPException(
                    status_code=500,
                    detail="Parsing succeeded but returned empty text content"
                )

            if not result.markdown or not result.markdown.strip():
                print(f"DEBUG: Parse returned empty markdown content!")
                raise HTTPException(
                    status_code=500,
                    detail="Parsing succeeded but returned empty markdown content"
                )

            # Write output files
            try:
                text_path, markdown_path = OutputWriter.write_output(
                    result.text, result.markdown, filename
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to write output files: {str(e)}"
                )

            # Create response
            return self._create_response(result, text_path, markdown_path)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Clean up temporary file
            FileValidator.cleanup_temp_file(temp_path)

    async def _save_uploaded_file(self, file: UploadFile, temp_path: str) -> None:
        """Save uploaded file to temporary location with basic integrity checking."""
        try:
            # Reset file pointer to beginning
            await file.seek(0)

            # Read the file content
            content = await file.read()

            # Basic validation for Office documents
            file_ext = os.path.splitext(temp_path)[1].lower()
            if file_ext in ['.docx', '.xlsx', '.pptx']:
                # Check ZIP signature (Office docs are ZIP files)
                if len(content) < 2 or content[:2] != b'PK':
                    raise RuntimeError(f"Invalid {file_ext} file format")

            # Write to temporary file
            with open(temp_path, "wb") as buffer:
                buffer.write(content)
                buffer.flush()
                os.fsync(buffer.fileno())

            # Verify file was written
            if os.path.exists(temp_path):
                written_size = os.path.getsize(temp_path)
                if written_size != len(content):
                    raise RuntimeError(f"File size mismatch: expected {len(content)}, got {written_size}")
            else:
                raise RuntimeError(f"Temporary file was not created: {temp_path}")

            # Reset file pointer
            await file.seek(0)

        except Exception as e:
            raise RuntimeError(f"Failed to save uploaded file: {str(e)}")

    def _create_response(self, result: ParseResult, text_path: str, markdown_path: str) -> Dict[str, Any]:
        """Create response dictionary from parse result."""
        return {
            "filename": result.filename,
            "engine": result.engine,
            "text_preview": result.get_text_preview(PREVIEW_LENGTH),
            "markdown_preview": result.get_markdown_preview(PREVIEW_LENGTH),
            "message": f"Parsed and saved to {text_path} and {markdown_path}",
            "output_files": {
                "text": text_path,
                "markdown": markdown_path
            }
        }

    def get_supported_engines(self) -> Dict[str, Any]:
        """Get information about supported parser engines."""
        # Check LlamaParse configuration safely
        llama_configured = False
        try:
            llama_configured = self.llamaparse_service.validate_configuration()
        except:
            llama_configured = False

        return {
            "engines": [
                {
                    "name": ParserEngine.DOCLING,
                    "description": "Open-source document parsing using Docling",
                    "supported_formats": [".pdf", ".docx", ".csv", ".xlsx", ".pptx"],
                    "status": "available"
                },
                {
                    "name": ParserEngine.LLAMA,
                    "description": "Cloud-based parsing using LlamaParse",
                    "supported_formats": ["Most document formats"],
                    "requires_api_key": True,
                    "configured": llama_configured,
                    "status": "available" if llama_configured else "requires_api_key"
                }
            ]
        }
