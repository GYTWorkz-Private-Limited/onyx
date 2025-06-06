# DataUpload - S3 Bucket Upload Service

A modular, production-ready FastAPI service for uploading files to Amazon S3 with concurrent processing capabilities. This service is part of the Pulse project ecosystem and follows the established modular architecture patterns with separated API and controller layers.

## 🏗️ Architecture

The service follows the Pulse project's modular architecture with clean separation of concerns:

```
S3Bucket/
├── api/                 # API routes and endpoint definitions
│   ├── __init__.py
│   └── routes.py        # FastAPI route definitions
├── controllers/         # Request handling and business logic coordination
│   ├── __init__.py
│   └── upload_controller.py  # Upload business logic
├── services/            # Core business logic
│   └── s3_upload_service.py  # S3 operations and file handling
├── models/              # Pydantic data models and schemas
│   ├── __init__.py
│   └── upload_models.py # Upload request/response models
├── utils/               # Utility functions and helpers
│   ├── logger.py        # Logging configuration
│   └── validators.py    # File validation utilities
├── config/              # Configuration management
│   └── settings.py      # Environment-based settings
├── datafolder/          # Sample data files for testing
├── server.py            # Main FastAPI application
├── pyproject.toml       # Poetry dependency management
├── poetry.lock          # Poetry lock file
└── README.md           # This documentation
```

### Architecture Principles
- **Modular Design**: Each component has a single responsibility
- **API/Controller Separation**: Clean separation between API routes and business logic
- **Service Layer**: Encapsulated business logic in dedicated service classes
- **Configuration Management**: Centralized settings with environment variable support
- **Poetry Integration**: Modern Python dependency management following Pulse guidelines

### 🔄 Separation of Concerns
- **API Layer** (`api/routes.py`): Handles HTTP requests/responses and route definitions
- **Controller Layer** (`controllers/`): Contains business logic and orchestrates services
- **Service Layer** (`services/`): Core S3 operations and file handling
- **Models Layer** (`models/`): Data validation and response schemas
- **Utils Layer** (`utils/`): Reusable utilities and validation functions

## ✨ Features

- **Modular Design**: Clean separation of concerns with controllers, services, and utilities
- **Concurrent Processing**: Optimized batch uploads with configurable concurrency
- **Comprehensive Validation**: File size, type, and naming validation
- **Structured Logging**: Detailed logging with configurable levels
- **Error Handling**: Robust error handling with structured responses
- **Health Monitoring**: Health check endpoints for service monitoring
- **Configuration Management**: Environment-based configuration with validation

## 🚀 Quick Start

### 1. Install Dependencies with Poetry
Following Pulse project guidelines, this service uses Poetry for dependency management:

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Navigate to the S3Bucket directory
cd onyx/pulse/DataUpload/S3Bucket

# Install project dependencies
poetry install

# Activate the virtual environment
poetry shell
```

**Alternative: Using pip (not recommended)**
```bash
pip install -r requirements.txt  # If requirements.txt exists
```

### 3. Environment Configuration
Create a `.env` file:
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name

# Upload Configuration
MAX_CONCURRENT_UPLOADS=10
MAX_FILE_SIZE_MB=100
ALLOWED_FILE_EXTENSIONS=.txt,.csv,.json,.xlsx,.pdf,.jpg,.png,.docx,.py

# API Configuration
API_HOST=0.0.0.0
API_PORT=8889
LOG_LEVEL=INFO
```

### 3. Run the Service

**Using Poetry (recommended):**
```bash
# Run with Poetry
poetry run python server.py

# Or activate the environment first
poetry shell
python server.py
```

**Using Poetry scripts (if configured):**
```bash
poetry run start-server
```

**Direct execution:**
```bash
python server.py
```

The service will be available at:
- **API**: http://localhost:8889
- **Documentation**: http://localhost:8889/docs (Swagger UI)
- **ReDoc**: http://localhost:8889/redoc (Alternative documentation)
- **Health Check**: http://localhost:8889/upload/health
- **Service Info**: http://localhost:8889/

## 📚 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service information and available endpoints |
| GET | `/ping` | Simple connectivity test |
| GET | `/upload/health` | Health check with S3 connectivity |

### Upload Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload/` | Upload multiple files to S3 |

### API Documentation
- **Interactive Docs**: http://localhost:8889/docs (Swagger UI)
- **ReDoc**: http://localhost:8889/redoc (Alternative documentation)

### Upload Request

**Parameters:**
- `files`: List of files (multipart/form-data)
- `project_name`: Project folder name in S3 (required)
- `s3_prefix`: Optional prefix path within project (optional)

**Example Response:**
```json
{
  "status": "success",
  "summary": "5 of 5 files uploaded successfully in 2.34 seconds",
  "uploaded_files": [
    {
      "filename": "document.pdf",
      "s3_path": "s3://bucket/projects/my-project/documents/document.pdf",
      "status": "success",
      "file_size": 1024000,
      "upload_time": "2024-01-15T10:30:00"
    }
  ],
  "total_files": 5,
  "successful_uploads": 5,
  "failed_uploads": 0,
  "project_name": "my-project",
  "s3_prefix": "documents"
}
```

## 🔧 Usage Examples

### Upload Multiple Files
```bash
curl -X POST "http://localhost:8889/upload/" \
  -F "files=@document1.pdf" \
  -F "files=@image.jpg" \
  -F "files=@data.csv" \
  -F "project_name=my-project" \
  -F "s3_prefix=uploads/batch1"
```

### Health Check
```bash
curl http://localhost:8889/upload/health
```

### Service Information
```bash
curl http://localhost:8889/
```

### Using Poetry for Development
```bash
# Run tests (when implemented)
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=.

# Format code (if black is added)
poetry run black .

# Lint code (if flake8 is added)
poetry run flake8

# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET_NAME` | S3 bucket name | Required |
| `MAX_CONCURRENT_UPLOADS` | Max concurrent uploads | `10` |
| `MAX_FILE_SIZE_MB` | Max file size in MB | `100` |
| `ALLOWED_FILE_EXTENSIONS` | Comma-separated extensions | See config |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8889` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FILE` | Optional log file path | None |

## 🏃‍♂️ Running in Production

### Using Gunicorn with Poetry
```bash
# Install gunicorn as a dev dependency
poetry add --group dev gunicorn

# Run with Gunicorn
poetry run gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8889
```

### Using Docker with Poetry
```dockerfile
FROM python:3.11-slim

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Configure Poetry: Don't create virtual environment (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only=main

# Copy application code
COPY . .

# Expose port
EXPOSE 8889

# Run the application
CMD ["poetry", "run", "python", "server.py"]
```

### Using systemd (Linux) with Poetry
```ini
[Unit]
Description=S3 Upload Service
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/app
Environment=PATH=/app/.venv/bin
ExecStart=/usr/local/bin/poetry run python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Alternative: Export requirements.txt for Docker
```bash
# Export dependencies to requirements.txt for Docker builds
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## 🧪 Testing

### Unit Tests with Poetry
```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=.

# Run specific test file
poetry run pytest tests/test_upload.py

# Run tests in verbose mode
poetry run pytest -v
```

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8889/upload/health

# Test upload functionality with sample files
curl -X POST "http://localhost:8889/upload/" \
  -F "files=@datafolder/sample.pdf" \
  -F "files=@datafolder/image.jpg" \
  -F "project_name=test-project" \
  -F "s3_prefix=uploads"

# Test service info
curl http://localhost:8889/
```

### Development Testing
```bash
# Install development dependencies
poetry install

# Run linting (if flake8 is added)
poetry run flake8

# Format code (if black is added)
poetry run black .

# Type checking (if mypy is added)
poetry run mypy .
```

### Development Dependencies
The project includes development dependencies for testing:
- `pytest`: Testing framework
- `pytest-asyncio`: Async testing support
- `httpx`: HTTP client for testing API endpoints

## 🛠️ Development Workflow

### Adding New Dependencies
```bash
# Add production dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show dependency tree
poetry show --tree
```

### Code Structure Guidelines
- **Routes** (`api/routes.py`): Keep route definitions clean, delegate to controllers
- **Controllers** (`controllers/`): Handle business logic, orchestrate services
- **Services** (`services/`): Core functionality, reusable business operations
- **Models** (`models/`): Data validation and serialization
- **Utils** (`utils/`): Helper functions and utilities

### Sample Data
The `datafolder/` contains sample files for testing:
- Various file formats (PDF, DOCX, CSV, JSON, images, etc.)
- Use these files to test upload functionality
- Validate different file types and sizes

## 📝 Logging

The service provides structured logging with:
- Request/response logging
- Upload progress tracking
- Error details and stack traces
- Performance metrics

## 🔒 Security Considerations

- **File Validation**: Validate file types and sizes before upload
- **Filename Sanitization**: Sanitize filenames to prevent path traversal
- **IAM Permissions**: Use IAM roles with minimal S3 permissions
- **CORS Configuration**: Configure CORS appropriately for production
- **Rate Limiting**: Consider implementing rate limiting for public deployments
- **Access Control**: Implement authentication for production deployments
- **Network Security**: Configure appropriate firewall rules

## 🚀 Integration with Pulse Project

This service is designed to integrate seamlessly with the Pulse project ecosystem:

### Pulse Architecture Compliance
- **Modular Structure**: Follows the established Pulse modular architecture
- **Poetry Integration**: Uses Poetry for dependency management as per Pulse guidelines
- **API Standards**: Implements FastAPI with consistent endpoint patterns
- **Configuration Management**: Environment-based configuration following Pulse patterns

### Team-Friendly Usage
This connector provides simple, team-friendly integration for development teams:

```python
# Example integration in client applications
import requests
import os

# Health check
response = requests.get("http://localhost:8889/upload/health")
print(response.json())

# Upload files
files = [
    ('files', ('document.pdf', open('document.pdf', 'rb'), 'application/pdf')),
    ('files', ('image.jpg', open('image.jpg', 'rb'), 'image/jpeg'))
]
data = {
    'project_name': 'my-project',
    's3_prefix': 'uploads/batch1'
}

response = requests.post("http://localhost:8889/upload/", files=files, data=data)
print(response.json())

# Close file handles
for _, (_, file_obj, _) in files:
    file_obj.close()
```

### Development Team Guidelines
1. **Environment Setup**: Use Poetry for consistent dependency management
2. **Testing**: Run tests before committing changes using sample data in `datafolder/`
3. **Code Quality**: Use provided linting and formatting tools
4. **Documentation**: Update README when adding new features
5. **API Design**: Follow existing endpoint patterns for consistency

## 🎯 Benefits of This Architecture

- **Concurrent Processing**: Optimized batch uploads with configurable concurrency
- **Comprehensive Validation**: File size, type, and naming validation
- **Simplified Maintenance**: Clean modular structure reduces bugs
- **Team Collaboration**: Consistent patterns across Pulse project
- **Easy Integration**: Simple API for client/backend applications
- **Sample Data Ready**: Includes test files for immediate development
