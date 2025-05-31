# DataSync - S3 Bucket Synchronization Service

A modular, production-ready FastAPI service for real-time S3 file synchronization with AWS Lambda integration. This service is part of the Pulse project ecosystem and follows the established modular architecture patterns.

## 🏗️ Architecture

The service follows the Pulse project's modular architecture with clean separation of concerns:

```
S3Bucket/
├── api/                 # API routes and endpoint definitions
│   ├── __init__.py
│   └── routes.py
├── controllers/         # Request handling and business logic coordination
│   └── sync_controller.py
├── services/           # Core business logic
│   ├── s3_sync_service.py
│   └── file_service.py
├── models/             # Pydantic data models and schemas
│   └── s3_models.py
├── utils/              # Utility functions and helpers
│   ├── logger.py
│   └── file_utils.py
├── config/             # Configuration management
│   └── settings.py
├── lambda/             # AWS Lambda functions
│   └── s3_lambda_handler.py
├── server.py           # Main FastAPI application
├── pyproject.toml      # Poetry dependency management
├── poetry.lock         # Poetry lock file
└── README.md          # This documentation
```

### Architecture Principles
- **Modular Design**: Each component has a single responsibility
- **API/Controller Separation**: Clean separation between API routes and business logic
- **Service Layer**: Encapsulated business logic in dedicated service classes
- **Configuration Management**: Centralized settings with environment variable support
- **Poetry Integration**: Modern Python dependency management following Pulse guidelines

## ✨ Features

- **Modular Design**: Clean separation of concerns with controllers, services, and utilities
- **Real-time Sync**: Instant file synchronization via S3 event notifications
- **Periodic Sync**: Configurable full synchronization intervals
- **File Integrity**: Optional file integrity verification using checksums
- **Smart Skipping**: Skip downloads for existing files that haven't changed
- **Health Monitoring**: Comprehensive health checks and monitoring endpoints
- **Error Handling**: Robust error handling with retry mechanisms
- **AWS Lambda Integration**: Production-ready Lambda handler for S3 events

## 🚀 Quick Start

### 1. Install Dependencies with Poetry
Following Pulse project guidelines, this service uses Poetry for dependency management:

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate the virtual environment
poetry shell
```

**Alternative: Using pip (not recommended)**
```bash
pip install -r requirements.txt  # If requirements.txt exists
```

### 2. Environment Configuration
Create a `.env` file:
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name

# Sync Configuration
LOCAL_DOWNLOAD_DIR=downloaded_files
SYNC_INTERVAL_HOURS=1.0
ENABLE_PERIODIC_SYNC=true
MAX_FILE_SIZE_MB=1000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8888
LOG_LEVEL=INFO
LOG_FILE=s3_notifications.log

# Performance Configuration
SKIP_EXISTING_FILES=true
VERIFY_FILE_INTEGRITY=true
DOWNLOAD_TIMEOUT_SECONDS=300
RETRY_ATTEMPTS=3
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

**Using Poetry scripts:**
```bash
poetry run start-server
```

**Direct execution:**
```bash
python server.py
```

The service will be available at:
- **API**: http://localhost:8888
- **Documentation**: http://localhost:8888/docs
- **Health Check**: http://localhost:8888/sync/health
- **Service Info**: http://localhost:8888/

## 📚 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service information and available endpoints |
| GET | `/ping` | Simple connectivity test |
| GET | `/sync/health` | Health check with S3 connectivity |
| GET | `/sync/config` | Current sync configuration |
| GET | `/sync/stats` | Synchronization statistics |

### Sync Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync/trigger` | Trigger manual sync |
| POST | `/sync/s3-notification` | Receive S3 event notifications |
| GET | `/sync/files` | List files from S3 or local storage |
| GET | `/sync/download/{file_path}` | Download file from local cache |

### API Documentation
- **Interactive Docs**: http://localhost:8888/docs (Swagger UI)
- **ReDoc**: http://localhost:8888/redoc (Alternative documentation)

### Example Responses

**Health Check:**
```json
{
  "status": "healthy",
  "message": "S3 Sync Service is running and all connections are active",
  "s3_connection": true,
  "download_directory": "/app/downloaded_files",
  "directory_writable": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

**Sync Response:**
```json
{
  "status": "success",
  "message": "Synced 15 of 15 files in 3.45 seconds",
  "processed_files": 15,
  "successful_operations": 15,
  "failed_operations": 0,
  "sync_details": [
    {
      "operation": "download",
      "file_key": "projects/my-project/document.pdf",
      "status": "success",
      "message": "Downloaded successfully in 0.23 seconds"
    }
  ]
}
```

## 🔧 Usage Examples

### Manual Sync
```bash
# Sync all files
curl -X POST "http://localhost:8888/sync/trigger"

# Sync files with prefix
curl -X POST "http://localhost:8888/sync/trigger?prefix=projects/my-project"

# Background sync
curl -X POST "http://localhost:8888/sync/trigger?background=true"
```

### List Files
```bash
# List S3 files
curl "http://localhost:8888/sync/files?source=s3&prefix=projects/"

# List local files
curl "http://localhost:8888/sync/files?source=local"
```

### Download File
```bash
curl "http://localhost:8888/sync/download/projects/my-project/document.pdf"
```

### Health Check
```bash
curl "http://localhost:8888/sync/health"
```

### Using Poetry for Development
```bash
# Run tests (when implemented)
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run flake8

# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name
```

## 🔗 AWS Lambda Integration

### 1. Deploy Lambda Function
Use the provided `lambda/s3_lambda_handler.py` as your Lambda function:

```python
# The handler is already production-ready with:
# - Comprehensive error handling
# - Retry mechanisms with exponential backoff
# - Event validation
# - Structured logging
```

### 2. Lambda Environment Variables
```env
API_ENDPOINT=https://your-sync-service.com
TIMEOUT_SECONDS=30
RETRY_ATTEMPTS=3
```

### 3. S3 Event Configuration
Configure your S3 bucket to trigger the Lambda function on:
- `ObjectCreated:*` events
- `ObjectRemoved:*` events

### 4. Lambda Permissions
Ensure your Lambda function has:
- S3 read permissions for the bucket
- Network access to your sync service API

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET_NAME` | S3 bucket name | Required |
| `LOCAL_DOWNLOAD_DIR` | Local download directory | `downloaded_files` |
| `SYNC_INTERVAL_HOURS` | Periodic sync interval | `1.0` |
| `ENABLE_PERIODIC_SYNC` | Enable periodic sync | `true` |
| `MAX_FILE_SIZE_MB` | Max file size in MB | `1000` |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8888` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FILE` | Log file path | `s3_notifications.log` |
| `SKIP_EXISTING_FILES` | Skip existing files | `true` |
| `VERIFY_FILE_INTEGRITY` | Verify file integrity | `true` |
| `DOWNLOAD_TIMEOUT_SECONDS` | Download timeout | `300` |
| `RETRY_ATTEMPTS` | Retry attempts | `3` |

## 🏃‍♂️ Running in Production

### Using Docker with Poetry
```dockerfile
FROM python:3.9-slim

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
EXPOSE 8888

# Run the application
CMD ["poetry", "run", "python", "server.py"]
```

### Using Gunicorn with Poetry
```bash
# Install gunicorn as a dev dependency
poetry add --group dev gunicorn

# Run with gunicorn
poetry run gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8888
```

### Using systemd (Linux) with Poetry
```ini
[Unit]
Description=S3 Sync Service
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

## 🧪 Testing

### Unit Tests with Poetry
```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=.

# Run specific test file
poetry run pytest tests/test_s3_sync.py

# Run tests in verbose mode
poetry run pytest -v
```

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8888/sync/health

# Test sync functionality
curl -X POST http://localhost:8888/sync/trigger

# Test file listing
curl http://localhost:8888/sync/files?source=s3

# Test service info
curl http://localhost:8888/
```

### Development Testing
```bash
# Install development dependencies
poetry install

# Run linting
poetry run flake8

# Format code
poetry run black .

# Type checking (if mypy is added)
poetry run mypy .
```

## 📝 Logging

The service provides comprehensive logging:
- **Request/Response**: All HTTP requests and responses
- **Sync Operations**: File download/delete operations with timing
- **Error Handling**: Detailed error messages and stack traces
- **Performance**: Operation timing and statistics
- **Health Monitoring**: Service health and connectivity status

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## 🔒 Security Considerations

- **AWS Credentials**: Use IAM roles instead of access keys when possible
- **Network Security**: Configure appropriate firewall rules
- **File Validation**: Validate file types and sizes
- **Access Control**: Implement authentication for production deployments
- **CORS Configuration**: Configure CORS appropriately for your environment
- **Rate Limiting**: Consider implementing rate limiting for public APIs

## 🚨 Troubleshooting

### Common Issues

1. **S3 Connection Failed**
   - Check AWS credentials and permissions
   - Verify S3 bucket exists and is accessible
   - Check network connectivity

2. **Download Directory Not Writable**
   - Check directory permissions
   - Ensure sufficient disk space
   - Verify directory path exists

3. **Lambda Function Timeout**
   - Increase Lambda timeout setting
   - Check API endpoint accessibility
   - Review Lambda logs for errors

4. **Files Not Syncing**
   - Check S3 event configuration
   - Verify Lambda function is triggered
   - Review service logs for errors

### Debug Mode
```env
LOG_LEVEL=DEBUG
```

## 📊 Monitoring

The service exposes several endpoints for monitoring:
- `/api/v1/health` - Health check
- `/api/v1/stats` - Sync statistics
- `/api/v1/config` - Current configuration


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

# Health check
response = requests.get("http://localhost:8888/sync/health")
print(response.json())

# Trigger sync
response = requests.post("http://localhost:8888/sync/trigger")
print(response.json())

# List files
response = requests.get("http://localhost:8888/sync/files?source=s3")
files = response.json()
```

### Development Team Guidelines
1. **Environment Setup**: Use Poetry for consistent dependency management
2. **Testing**: Run tests before committing changes
3. **Code Quality**: Use provided linting and formatting tools
4. **Documentation**: Update README when adding new features
5. **API Design**: Follow existing endpoint patterns for consistency

## 🎯 Benefits of This Architecture

- **Reduced Dependencies**: Optimized dependency management with Poetry
- **Lower Resource Usage**: Efficient memory and CPU usage
- **Faster Performance**: Streamlined code focuses on essential operations
- **Simplified Maintenance**: Clean modular structure reduces bugs
- **Team Collaboration**: Consistent patterns across Pulse project
- **Easy Integration**: Simple API for client/backend applications
