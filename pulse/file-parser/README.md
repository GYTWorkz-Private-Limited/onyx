# File Parser API

A production-ready document parsing service that converts various file formats into structured text and markdown using advanced parsing engines.

## ✨ Key Features

- **🚀 Production Ready**: Clean, optimized codebase with proper logging
- **📄 Multiple Formats**: PDF, DOCX, XLSX, PPTX, CSV support
- **⚡ High Performance**: Optimized processing with intelligent defaults
- **🌍 Universal Compatibility**: Works reliably across different systems
- **🔧 Two Parsing Engines**: Docling (open-source) and LlamaParse (cloud-based)
- **🛠️ RESTful API**: FastAPI-based with automatic documentation
- **📊 Structured Logging**: Production-grade logging with configurable levels

## 🚀 Quick Start

### Installation

```bash
git clone <repository-url>
cd file-parser
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and configure as needed:
```bash
cp .env.example .env
# Edit .env with your settings (optional - works with defaults)
```

### Usage

**Start the API server:**
```bash
python server.py
```

**Access the API documentation:**
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

**Parse a document:**
```bash
curl -X POST "http://localhost:8000/api/v1/parse/" \
     -F "file=@document.pdf" \
     -F "engine=docling"
```

## 📊 Performance

The system provides optimized processing for various document types:

| Document Type | Typical Processing Time | Features |
|---------------|------------------------|----------|
| **Simple PDF** (text-based) | 10-30 seconds | Fast text extraction |
| **Complex PDF** (scanned/images) | 1-3 minutes | OCR processing |
| **Office Documents** | 5-20 seconds | Native format support |
| **Large Files** (>50MB) | 2-5 minutes | Chunked processing |

## 📄 Supported Formats

| Format | Extension | Features |
|--------|-----------|----------|
| **PDF** | `.pdf` | OCR support, table extraction |
| **Word** | `.docx` | Full formatting preservation |
| **Excel** | `.xlsx`, `.xls` | Multi-sheet support |
| **PowerPoint** | `.pptx` | Text and table extraction |
| **CSV** | `.csv` | Structured data parsing |

## 🔧 Parsing Engines

### Docling (Recommended)
- **Free and open-source**
- **No API key required**
- **Optimized for performance**
- **OCR enabled for scanned documents**

### LlamaParse (Optional)
- **Cloud-based processing**
- **Higher accuracy for complex documents**
- **Requires API key** ([Get one here](https://cloud.llamaindex.ai/))

## ⚙️ Configuration

The system works with sensible defaults. Configure by editing your `.env` file:

```env
# Server Configuration
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=production

# LlamaParse API (Optional - for cloud-based parsing)
LLAMA_CLOUD_API_KEY=your_api_key_here

# File Processing
OUTPUT_DIR=output
MAX_FILE_SIZE_MB=100
ALLOWED_EXTENSIONS=pdf,docx,xlsx,pptx,csv

# Performance Tuning (Optional)
# PYTORCH_NUM_THREADS=6
# OMP_NUM_THREADS=6
# MKL_NUM_THREADS=6

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/file_parser.log
```

## 🌐 API Reference

### Parse Document

**Endpoint:** `POST /api/v1/parse/`

**Parameters:**
- `file`: Document file to parse (multipart/form-data)
- `engine`: `docling` (default) or `llama`

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "engine": "docling",
  "processing_time": 2.34,
  "text_preview": "First 500 characters of extracted text...",
  "files_created": [
    "output/document.md",
    "output/document.txt"
  ]
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

## 🏗️ Architecture

The service follows a clean, layered architecture:

1. **API Layer**: FastAPI routes with automatic validation
2. **Controller Layer**: Business logic and request handling
3. **Service Layer**: Parsing engines (Docling, LlamaParse)
4. **Model Layer**: Data structures and validation schemas
5. **Utility Layer**: Logging, file validation, and helpers

## 📁 Project Structure

```
file-parser/
├── api/                 # FastAPI routes and endpoints
│   └── parse_routes.py  # Document parsing endpoints
├── controllers/         # Business logic layer
│   └── parse_controller.py # Parse request handling
├── services/           # Core parsing engines
│   ├── base_parser.py   # Abstract base parser
│   ├── docling_service.py # Docling parsing engine
│   └── llamaparse_service.py # LlamaParse engine
├── models/             # Data models and structures
│   └── parse_models.py  # Parsing result models
├── schemas/            # API validation schemas
│   └── parse_schemas.py # Request/response schemas
├── utils/              # Utility modules
│   ├── constants.py     # Application constants
│   ├── file_validator.py # File validation logic
│   ├── logging_config.py # Logging configuration
│   └── output_writer.py # File output handling
├── logs/               # Application logs
├── output/             # Parsed document outputs
├── environment.py      # Environment configuration
├── server.py           # FastAPI application entry point
└── .env.example        # Environment variables template
```

## 🐛 Troubleshooting

**Import errors after installation?**
- Ensure you're in the correct directory and virtual environment
- Run `pip install -r requirements.txt` again
- Check Python version compatibility (3.8+)

**Parsing failures?**
- Check the logs in `logs/file_parser.log` for detailed error messages
- Verify file format is supported
- Try with a different parsing engine (`docling` vs `llama`)

**Performance issues?**
- Monitor system resources during processing
- Adjust thread settings in `.env` file if needed
- For very large files, consider splitting them

**API errors?**
- Check that the server is running on the correct port
- Verify file upload size limits
- Ensure proper multipart/form-data encoding

**Need help?**
- Check the application logs for detailed error information
- Review the API documentation at `/docs` endpoint
- Create an issue on GitHub with log details

## 📊 Logging

The application uses structured logging with configurable levels:

- **INFO**: General application flow and successful operations
- **DEBUG**: Detailed diagnostic information (disabled in production)
- **WARNING**: Potentially harmful situations
- **ERROR**: Error events that allow the application to continue

**Log Configuration:**
```env
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/file_parser.log
```

**Log Format:**
```
2024-01-01 12:00:00,000 - INFO - parse_controller - File parsing completed - {"filename": "document.pdf", "engine": "docling", "success": true}
```

## 🚀 Production Deployment

**Environment Setup:**
1. Set `ENVIRONMENT=production` in your `.env` file
2. Configure appropriate `LOG_LEVEL` (INFO or WARNING)
3. Set up proper CORS origins instead of allowing all
4. Configure file size limits and allowed extensions
5. Set up log rotation for the log files

**Security Considerations:**
- Configure CORS properly for your domain
- Set appropriate file size limits
- Validate file types beyond extensions
- Monitor log files for security events
- Use HTTPS in production

**Performance Monitoring:**
- Monitor memory usage during large file processing
- Set up alerts for processing failures
- Track API response times
- Monitor disk space for output files and logs

## 📄 License

MIT License - see LICENSE file for details.
