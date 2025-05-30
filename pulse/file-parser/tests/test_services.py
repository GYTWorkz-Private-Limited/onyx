"""Tests for parsing services."""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os

from services.docling_service import DoclingService
from services.llamaparse_service import LlamaParseService
from models.parse_models import ParserConfig


class TestDoclingService:
    """Test cases for DoclingService."""
    
    def test_init(self):
        """Test DoclingService initialization."""
        service = DoclingService()
        assert service.config.engine == "docling"
        assert service.converter is not None
    
    def test_is_supported(self):
        """Test file format support checking."""
        service = DoclingService()
        
        assert service.is_supported("test.pdf") == True
        assert service.is_supported("test.docx") == True
        assert service.is_supported("test.csv") == True
        assert service.is_supported("test.xlsx") == True
        assert service.is_supported("test.pptx") == True
        assert service.is_supported("test.txt") == False
    
    def test_unsupported_format(self):
        """Test parsing unsupported format raises error."""
        service = DoclingService()
        
        with pytest.raises(ValueError, match="Unsupported format"):
            service.parse("test.txt")
    
    @patch('services.docling_service.pd.read_csv')
    def test_parse_csv(self, mock_read_csv):
        """Test CSV parsing."""
        # Mock pandas DataFrame
        mock_df = MagicMock()
        mock_df.to_string.return_value = "col1,col2\nval1,val2"
        mock_df.to_markdown.return_value = "| col1 | col2 |\n|------|------|\n| val1 | val2 |"
        mock_read_csv.return_value = mock_df
        
        service = DoclingService()
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp.write(b"col1,col2\nval1,val2")
            tmp.flush()
            
            text, markdown = service.parse(tmp.name)
            
            assert "col1,col2" in text
            assert "| col1 | col2 |" in markdown
            
            os.unlink(tmp.name)


class TestLlamaParseService:
    """Test cases for LlamaParseService."""
    
    def test_init(self):
        """Test LlamaParseService initialization."""
        service = LlamaParseService()
        assert service.config.engine == "llama"
    
    def test_is_supported(self):
        """Test that LlamaParseService supports all formats."""
        service = LlamaParseService()
        
        assert service.is_supported("test.pdf") == True
        assert service.is_supported("test.docx") == True
        assert service.is_supported("test.txt") == True  # LlamaParse is more flexible
    
    @patch('environment.Environment.validate_llama_config')
    def test_validate_configuration(self, mock_validate):
        """Test configuration validation."""
        mock_validate.return_value = True
        
        service = LlamaParseService()
        assert service.validate_configuration() == True
        
        mock_validate.return_value = False
        assert service.validate_configuration() == False
    
    def test_get_parser_info(self):
        """Test getting parser information."""
        service = LlamaParseService()
        info = service.get_parser_info()
        
        assert info["engine"] == "llama"
        assert "output_format" in info
        assert "mode" in info
        assert "api_key_configured" in info
