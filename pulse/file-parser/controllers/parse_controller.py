"""Parse controller for handling file parsing business logic."""

import os
import shutil
from typing import Dict, Any
from fastapi import UploadFile, HTTPException

from models.parse_models import ParseResult, ParserConfig
from services.docling_service import DoclingService
from services.llamaparse_service import LlamaParseService
from tools.file_validator import FileValidator
from tools.output_writer import OutputWriter
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
            self._docling_service = DoclingService()
        return self._docling_service
    
    @property
    def llamaparse_service(self) -> LlamaParseService:
        """Get or create LlamaParse service instance."""
        if self._llamaparse_service is None:
            self._llamaparse_service = LlamaParseService()
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
            
            # Get parser service
            parser_service = self.get_parser_service(engine)
            
            # Parse the file
            result = parser_service.parse_to_result(temp_path, filename)
            
            if not result.success:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Parsing failed: {result.error_message}"
                )
            
            # Write output files
            text_path, markdown_path = OutputWriter.write_output(
                result.text, result.markdown, filename
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
        """Save uploaded file to temporary location."""
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
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
        return {
            "engines": [
                {
                    "name": ParserEngine.DOCLING,
                    "description": "Open-source document parsing using Docling",
                    "supported_formats": [".pdf", ".docx", ".csv", ".xlsx", ".pptx"]
                },
                {
                    "name": ParserEngine.LLAMA,
                    "description": "Cloud-based parsing using LlamaParse",
                    "supported_formats": ["Most document formats"],
                    "requires_api_key": True,
                    "configured": self.llamaparse_service.validate_configuration()
                }
            ]
        }
