"""Pydantic schemas for parse operations."""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum


class ParserEngine(str, Enum):
    """Available parser engines."""
    DOCLING = "docling"
    LLAMA = "llama"


class ParseRequest(BaseModel):
    """Request schema for file parsing."""
    engine: ParserEngine = Field(
        default=ParserEngine.LLAMA,
        description="Parser engine to use for processing the file"
    )


class ParseResponse(BaseModel):
    """Response schema for successful file parsing."""
    filename: str = Field(description="Name of the processed file")
    engine: str = Field(description="Parser engine used")
    text_preview: str = Field(description="Preview of extracted text")
    markdown_preview: str = Field(description="Preview of extracted markdown")
    message: str = Field(description="Success message with output file paths")
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "document.pdf",
                "engine": "llama",
                "text_preview": "This is a preview of the extracted text...",
                "markdown_preview": "# This is a preview of the extracted markdown...",
                "message": "Parsed and saved to output/document.txt and .md"
            }
        }


class ErrorResponse(BaseModel):
    """Response schema for errors."""
    detail: str = Field(description="Error message")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Unsupported file format."
            }
        }


class FileInfo(BaseModel):
    """File information schema."""
    filename: str
    size: int
    content_type: Optional[str] = None
