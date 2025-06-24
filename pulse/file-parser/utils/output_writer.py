"""Output writing utilities."""

import os
from pathlib import Path
from typing import Tuple

from environment import Environment


class OutputWriter:
    """Utilities for writing parsed output to files."""

    @staticmethod
    def write_output(text: str, markdown: str, filename: str) -> Tuple[str, str]:
        """
        Write parsed text and markdown to output files.

        Args:
            text: Plain text content
            markdown: Markdown content
            filename: Original filename

        Returns:
            Tuple[str, str]: (text_file_path, markdown_file_path)
        """
        # Ensure output directory exists
        OutputWriter.ensure_output_directory()

        output_dir = Environment.get_output_dir()
        name = Path(filename).stem

        text_path = os.path.join(output_dir, f"{name}.txt")
        markdown_path = os.path.join(output_dir, f"{name}.md")

        # Write text file
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Write markdown file
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        return text_path, markdown_path

    @staticmethod
    def get_output_paths(filename: str) -> Tuple[str, str]:
        """
        Get output file paths without writing.

        Args:
            filename: Original filename

        Returns:
            Tuple[str, str]: (text_file_path, markdown_file_path)
        """
        output_dir = Environment.get_output_dir()
        name = Path(filename).stem

        text_path = os.path.join(output_dir, f"{name}.txt")
        markdown_path = os.path.join(output_dir, f"{name}.md")

        return text_path, markdown_path

    @staticmethod
    def ensure_output_directory() -> None:
        """Ensure output directory exists."""
        output_dir = Environment.get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
