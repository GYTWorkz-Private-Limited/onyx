"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import patch

from server import app
from environment import Environment


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    # This would create a simple PDF file for testing
    # For now, we'll just return a path
    return "tests/fixtures/sample.pdf"


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    with patch.object(Environment, 'OUTPUT_DIR', 'test_output'), \
         patch.object(Environment, 'TEMP_DIR', 'test_temp'), \
         patch.object(Environment, 'LLAMA_CLOUD_API_KEY', 'test-key'):
        yield


@pytest.fixture(autouse=True)
def setup_test_directories():
    """Ensure test directories exist."""
    os.makedirs('test_output', exist_ok=True)
    os.makedirs('test_temp', exist_ok=True)
    yield
    # Cleanup is handled by tempfile or manual cleanup if needed
