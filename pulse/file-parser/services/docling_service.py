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
        self.converter = None  # Lazy initialization

    def _get_converter(self):
        """Get or create DocumentConverter instance."""
        if self.converter is None:
            try:
                self.converter = DocumentConverter()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Docling DocumentConverter: {str(e)}")
        return self.converter

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
        """Parse PDF using Docling local installation."""
        try:
            from docling.datamodel.document import DocumentConversionInput
            from pathlib import Path

            converter = self._get_converter()

            # Create proper DocumentConversionInput from file path
            input_doc = DocumentConversionInput.from_paths([Path(file_path)])

            # Convert the document
            conversion_results = converter.convert(input_doc)

            # Process the results (should be a generator)
            conversion_result = None
            for result in conversion_results:
                conversion_result = result
                break  # Take the first result

            if conversion_result is None:
                raise ValueError("Docling returned no results for PDF")

            # Export content using ConversionResult's render methods
            plain_text = conversion_result.render_as_text()
            markdown = conversion_result.render_as_markdown()

            if not plain_text or not plain_text.strip():
                raise ValueError("Docling extracted no text from the PDF")

            return plain_text, markdown

        except Exception as e:
            raise RuntimeError(f"PDF parsing failed: {str(e)}")

    def _parse_docx(self, file_path: str) -> Tuple[str, str]:
        """Parse DOCX using python-docx."""
        try:
            doc = DocxDocument(file_path)

            # Extract text from paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():  # Only include non-empty paragraphs
                    paragraphs.append(paragraph.text.strip())

            # Extract text from tables
            tables_text = []
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        row_data.append(cell_text)
                    if any(row_data):  # Only include non-empty rows
                        table_data.append(" | ".join(row_data))

                if table_data:
                    tables_text.append("\n".join(table_data))

            # Combine all text
            all_text = []
            if paragraphs:
                all_text.extend(paragraphs)
            if tables_text:
                all_text.extend(tables_text)

            text = "\n\n".join(all_text)

            # Create markdown version
            markdown_parts = []
            if paragraphs:
                markdown_parts.extend(paragraphs)
            if tables_text:
                # Convert tables to markdown format
                for table_text in tables_text:
                    lines = table_text.split("\n")
                    if len(lines) > 1:
                        # Add markdown table header separator
                        header = lines[0]
                        separator = " | ".join(["---"] * len(header.split(" | ")))
                        markdown_table = f"{header}\n{separator}\n" + "\n".join(lines[1:])
                        markdown_parts.append(markdown_table)
                    else:
                        markdown_parts.append(table_text)

            markdown = "\n\n".join(markdown_parts)

            if not text.strip():
                raise ValueError("No text content found in DOCX file")

            return text, markdown

        except Exception as e:
            raise RuntimeError(f"DOCX parsing failed: {str(e)}")

    def _parse_csv(self, file_path: str) -> Tuple[str, str]:
        """Parse CSV using pandas."""
        df = pd.read_csv(file_path)
        text = df.to_string(index=False)
        markdown = df.to_markdown(index=False)
        return text, markdown

    def _parse_excel(self, file_path: str) -> Tuple[str, str]:
        """Parse Excel files using pandas."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)

            if not excel_file.sheet_names:
                raise ValueError("No sheets found in Excel file")

            sheets_content = []

            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)

                    if df.empty:
                        continue

                    # Create content for this sheet
                    sheet_text = df.to_string(index=False)
                    sheet_markdown = df.to_markdown(index=False)

                    if len(excel_file.sheet_names) > 1:
                        # Multiple sheets - add headers
                        text_content = f"Sheet: {sheet_name}\n{'-' * 20}\n{sheet_text}"
                        markdown_content = f"## Sheet: {sheet_name}\n\n{sheet_markdown}"
                    else:
                        # Single sheet - no headers needed
                        text_content = sheet_text
                        markdown_content = sheet_markdown

                    sheets_content.append((text_content, markdown_content))

                except Exception as e:
                    # Skip problematic sheets but continue with others
                    continue

            if not sheets_content:
                raise ValueError("No readable data found in Excel file")

            # Combine all sheets
            text_parts = [content[0] for content in sheets_content]
            markdown_parts = [content[1] for content in sheets_content]

            text = "\n\n".join(text_parts)
            markdown = "\n\n".join(markdown_parts)

            return text, markdown

        except Exception as e:
            raise RuntimeError(f"Excel parsing failed: {str(e)}")

    def _parse_pptx(self, file_path: str) -> Tuple[str, str]:
        """Parse PPTX using python-pptx."""
        try:
            prs = pptx.Presentation(file_path)

            slides_content = []

            for slide_num, slide in enumerate(prs.slides, 1):
                slide_texts = []

                # Extract text from all shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_texts.append(shape.text.strip())

                    # Extract text from tables in shapes
                    if hasattr(shape, "table"):
                        table_data = []
                        for row in shape.table.rows:
                            row_data = []
                            for cell in row.cells:
                                if cell.text.strip():
                                    row_data.append(cell.text.strip())
                            if row_data:
                                table_data.append(" | ".join(row_data))
                        if table_data:
                            slide_texts.append("\n".join(table_data))

                if slide_texts:
                    slide_content = f"## Slide {slide_num}\n\n" + "\n\n".join(slide_texts)
                    slides_content.append(slide_content)

            if not slides_content:
                raise ValueError("No text content found in PPTX file")

            # Create text version (without markdown headers)
            text_parts = []
            for slide_content in slides_content:
                # Remove markdown headers for plain text
                lines = slide_content.split("\n")
                text_lines = [line for line in lines if not line.startswith("## Slide")]
                text_parts.append("\n".join(text_lines).strip())

            text = "\n\n---\n\n".join(text_parts)

            # Markdown version keeps the slide headers
            markdown = "\n\n".join(slides_content)

            return text, markdown

        except Exception as e:
            raise RuntimeError(f"PPTX parsing failed: {str(e)}")
