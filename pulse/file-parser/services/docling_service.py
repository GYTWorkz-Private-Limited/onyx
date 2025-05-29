"""Docling parsing service."""

import pandas as pd
from docling.document_converter import DocumentConverter
from docx import Document as DocxDocument
import pptx
from pathlib import Path
from typing import Tuple

from .base_parser import BaseParser
from models.parse_models import ParserConfig
from utils.constants import SUPPORTED_EXTENSIONS


class DoclingService(BaseParser):
    """Docling-based file parsing service."""
    
    def __init__(self, config: ParserConfig = None):
        """Initialize Docling service."""
        if config is None:
            config = ParserConfig(engine="docling")
        super().__init__(config)
        self.converter = DocumentConverter()
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported by Docling."""
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_EXTENSIONS
    
    def parse(self, file_path: str) -> Tuple[str, str]:
        """
        Parse file using Docling and various libraries.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Tuple[str, str]: (text_content, markdown_content)
            
        Raises:
            ValueError: If file format is not supported
            RuntimeError: If parsing fails
        """
        ext = Path(file_path).suffix.lower()
        
        if not self.is_supported(file_path):
            raise ValueError(f"Unsupported format: {ext}")
        
        try:
            if ext == ".pdf":
                return self._parse_pdf(file_path)
            elif ext == ".docx":
                return self._parse_docx(file_path)
            elif ext == ".csv":
                return self._parse_csv(file_path)
            elif ext in [".xls", ".xlsx"]:
                return self._parse_excel(file_path)
            elif ext == ".pptx":
                return self._parse_pptx(file_path)
            else:
                raise ValueError(f"Unsupported format: {ext}")
        except Exception as e:
            raise RuntimeError(f"Docling failed to parse {ext} file: {str(e)}")
    
    def _parse_pdf(self, file_path: str) -> Tuple[str, str]:
        """Parse PDF using Docling."""
        try:
            result = self.converter.convert(file_path)
            doc = result.document
            
            plain_text = doc.export_to_text()
            markdown = doc.export_to_markdown()
            
            if not plain_text.strip():
                raise ValueError("Docling extracted no text from the PDF.")
            
            return plain_text, markdown
        except Exception as e:
            raise RuntimeError(f"PDF parsing failed: {str(e)}")
    
    def _parse_docx(self, file_path: str) -> Tuple[str, str]:
        """Parse DOCX using python-docx."""
        doc = DocxDocument(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        markdown = text.replace("\n", "  \n")  # Convert to markdown line breaks
        return text, markdown
    
    def _parse_csv(self, file_path: str) -> Tuple[str, str]:
        """Parse CSV using pandas."""
        df = pd.read_csv(file_path)
        text = df.to_string(index=False)
        markdown = df.to_markdown(index=False)
        return text, markdown
    
    def _parse_excel(self, file_path: str) -> Tuple[str, str]:
        """Parse Excel files using pandas."""
        df = pd.read_excel(file_path)
        text = df.to_string(index=False)
        markdown = df.to_markdown(index=False)
        return text, markdown
    
    def _parse_pptx(self, file_path: str) -> Tuple[str, str]:
        """Parse PPTX using python-pptx."""
        prs = pptx.Presentation(file_path)
        texts = [
            shape.text 
            for slide in prs.slides 
            for shape in slide.shapes 
            if hasattr(shape, "text")
        ]
        text = "\n".join(texts)
        markdown = text.replace("\n", "  \n")  # Convert to markdown line breaks
        return text, markdown
