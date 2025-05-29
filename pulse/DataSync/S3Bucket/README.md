# S3 Sync Service - Modular Architecture

A modular, production-ready FastAPI service for real-time S3 file synchronization with AWS Lambda integration.

## 🏗️ Architecture

The service follows a clean, modular architecture:

```
DataSync/
├── controllers/          # API endpoints and request handling
│   ├── __init__.py
│   └── sync_controller.py
├── services/            # Business logic
│   ├── __init__.py
│   ├── s3_sync_service.py
│   └── file_service.py
├── models/              # Pydantic models
│   ├── __init__.py
│   └── s3_models.py
├── utils/               # Utility functions
│   ├── __init__.py
│   ├── logger.py
│   └── file_utils.py
├── config/              # Configuration management
│   ├── __init__.py
│   └── settings.py
├── lambda/              # AWS Lambda functions
│   ├── __init__.py
│   └── s3_lambda_handler.py
├── server.py            # Main FastAPI application
├── requirements.txt     # Dependencies
└── README.md           # This file
```

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

### 1. Install Dependencies
```bash
pip install -r requirements.txt
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
```bash
python server.py
```

The service will be available at:
- **API**: http://localhost:8888
- **Documentation**: http://localhost:8888/docs
- **Health Check**: http://localhost:8888/api/v1/health

## 📚 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service information |
| GET | `/ping` | Simple connectivity test |
| GET | `/api/v1/health` | Health check with S3 connectivity |
| GET | `/api/v1/config` | Current sync configuration |
| GET | `/api/v1/stats` | Synchronization statistics |

### Sync Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sync` | Trigger manual sync |
| POST | `/api/v1/s3-notification` | Receive S3 event notifications |
| GET | `/api/v1/files` | List files from S3 or local storage |
| GET | `/api/v1/download/{file_path}` | Download file from local cache |

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
curl -X POST "http://localhost:8888/api/v1/sync"

# Sync files with prefix
curl -X POST "http://localhost:8888/api/v1/sync?prefix=projects/my-project"

# Background sync
curl -X POST "http://localhost:8888/api/v1/sync?background=true"
```

### List Files
```bash
# List S3 files
curl "http://localhost:8888/api/v1/files?source=s3&prefix=projects/"

# List local files
curl "http://localhost:8888/api/v1/files?source=local"
```

### Download File
```bash
curl "http://localhost:8888/api/v1/download/projects/my-project/document.pdf"
```

### Health Check
```bash
curl "http://localhost:8888/api/v1/health"
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

### Using Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8888
CMD ["python", "server.py"]
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8888
```

### Using systemd (Linux)
```ini
[Unit]
Description=S3 Sync Service
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/app
Environment=PATH=/app/venv/bin
ExecStart=/app/venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🧪 Testing

### Unit Tests
```bash
# Run tests (when implemented)
pytest tests/
```

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8888/api/v1/health

# Test sync functionality
curl -X POST http://localhost:8888/api/v1/sync

# Test file listing
curl http://localhost:8888/api/v1/files?source=s3
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


## Benefits of Optimization

- **Reduced Dependencies**: No need for additional libraries for file processing
- **Lower Resource Usage**: Less memory and CPU usage without file content processing
- **Faster Performance**: Streamlined code focuses only on essential operations
- **Simplified Maintenance**: Less code means fewer potential bugs and easier updates
