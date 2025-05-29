# S3 Upload Service - Modular Architecture

A modular, production-ready FastAPI service for uploading files to Amazon S3 with concurrent processing capabilities.

## 🏗️ Architecture

The service follows a clean, modular architecture:

```
DataUpload/
├── controllers/          # API endpoints and request handling
│   ├── __init__.py
│   └── upload_controller.py
├── services/            # Business logic
│   ├── __init__.py
│   └── s3_upload_service.py
├── models/              # Pydantic models
│   ├── __init__.py
│   └── upload_models.py
├── utils/               # Utility functions
│   ├── __init__.py
│   ├── logger.py
│   └── validators.py
├── config/              # Configuration management
│   ├── __init__.py
│   └── settings.py
├── server.py            # Main FastAPI application
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## ✨ Features

- **Modular Design**: Clean separation of concerns with controllers, services, and utilities
- **Concurrent Processing**: Optimized batch uploads with configurable concurrency
- **Comprehensive Validation**: File size, type, and naming validation
- **Structured Logging**: Detailed logging with configurable levels
- **Error Handling**: Robust error handling with structured responses
- **Health Monitoring**: Health check endpoints for service monitoring
- **Configuration Management**: Environment-based configuration with validation

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
```bash
python server.py
```

The service will be available at:
- **API**: http://localhost:8889
- **Documentation**: http://localhost:8889/docs
- **Health Check**: http://localhost:8889/api/v1/health

## 📚 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service information |
| GET | `/ping` | Simple connectivity test |
| GET | `/api/v1/health` | Health check with S3 connectivity |
| GET | `/api/v1/config` | Current upload configuration |

### Upload Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload multiple files |
| POST | `/api/v1/upload/single` | Upload single file |

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
curl -X POST "http://localhost:8889/api/v1/upload" \
  -F "files=@document1.pdf" \
  -F "files=@image.jpg" \
  -F "files=@data.csv" \
  -F "project_name=my-project" \
  -F "s3_prefix=uploads/batch1"
```

### Health Check
```bash
curl http://localhost:8889/api/v1/health
```

### Get Configuration
```bash
curl http://localhost:8889/api/v1/config
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

### Using Gunicorn
```bash
pip install gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8889
```

### Using Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "server.py"]
```

## 🧪 Testing

The service includes comprehensive validation and error handling. Test with various file types and sizes to ensure proper operation.

## 📝 Logging

The service provides structured logging with:
- Request/response logging
- Upload progress tracking
- Error details and stack traces
- Performance metrics

## 🔒 Security Considerations

- Validate file types and sizes
- Sanitize filenames
- Use IAM roles with minimal S3 permissions
- Configure CORS appropriately for production
- Consider rate limiting for public deployments
