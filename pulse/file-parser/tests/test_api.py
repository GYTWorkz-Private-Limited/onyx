"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io

from server import app


class TestParseAPI:
    """Test cases for the parse API endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "File Parser API"
    
    def test_get_engines(self, client: TestClient):
        """Test the engines endpoint."""
        response = client.get("/api/v1/engines/")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert len(data["engines"]) >= 2  # docling and llama
    
    def test_parse_file_missing_file(self, client: TestClient):
        """Test parse endpoint with missing file."""
        response = client.post("/api/v1/parse/")
        assert response.status_code == 422  # Validation error
    
    def test_parse_file_unsupported_format(self, client: TestClient):
        """Test parse endpoint with unsupported file format."""
        file_content = b"test content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        data = {"engine": "docling"}
        
        response = client.post("/api/v1/parse/", files=files, data=data)
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]
    
    @patch('controllers.parse_controller.ParseController.parse_file')
    def test_parse_file_success(self, mock_parse, client: TestClient):
        """Test successful file parsing."""
        # Mock the parse_file method
        mock_parse.return_value = {
            "filename": "test.pdf",
            "engine": "docling",
            "text_preview": "Sample text...",
            "markdown_preview": "# Sample markdown...",
            "message": "Parsed and saved to output/test.txt and .md"
        }
        
        file_content = b"fake pdf content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {"engine": "docling"}
        
        response = client.post("/api/v1/parse/", files=files, data=data)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["engine"] == "docling"
    
    def test_root_redirect(self, client: TestClient):
        """Test that root redirects to docs."""
        response = client.get("/", allow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/docs" in response.headers["location"]
