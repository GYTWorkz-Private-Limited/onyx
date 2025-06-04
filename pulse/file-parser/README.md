# File Parser API

A FastAPI service for parsing documents using Docling (open-source) or LlamaParse (cloud-based) engines. Extracts text and markdown from PDF, DOCX, CSV, XLSX, and PPTX files.

## Features

- **Multiple Parser Engines**: Choose between Docling (free) or LlamaParse (requires API key)
- **Format Support**: PDF, DOCX, CSV, XLSX, PPTX
- **Dual Output**: Plain text and Markdown formats
- **REST API**: Well-documented endpoints with Swagger UI
- **File Validation**: Size limits and format checking

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd file-parser

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configuration

Copy `.env.example` to `.env` and configure:

```env
# LlamaParse Configuration (optional - for cloud parsing)
LLAMA_CLOUD_API_KEY=your-api-key-here
PARSER_MODE=balanced
OUTPUT_FORMAT=markdown

# Application Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=true
MAX_FILE_SIZE=50000000
```

**Getting a LlamaParse API Key:**
1. Visit [LlamaIndex Cloud](https://cloud.llamaindex.ai/)
2. Sign up for an account
3. Generate an API key
4. Add it to your `.env` file

### 3. Run the Server

```bash
python server.py
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## API Usage

### Endpoints

- **POST `/api/v1/parse/`** - Parse uploaded file
- **GET `/api/v1/engines/`** - Get supported parser engines
- **GET `/docs`** - Interactive API documentation

### Parse a Document

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/parse/" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf" \
     -F "engine=docling"
```

**Using Python requests:**
```python
import requests

with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/parse/",
        files={"file": f},
        data={"engine": "docling"}
    )
print(response.json())
```

### Parser Engines

- **`docling`** - Free, open-source parser (no API key required)
- **`llama`** - Cloud-based LlamaParse (requires API key, higher accuracy)

### Output Files

Parsed files are saved to the `output/` directory:
- `filename.txt` - Plain text extraction
- `filename.md` - Markdown formatted extraction

## Project Structure

```
file-parser/
├── api/                    # API routes
├── controllers/            # Business logic
├── services/               # Parser implementations
├── models/                 # Data models
├── schemas/                # API schemas
├── utils/                  # Utilities
├── output/                 # Generated files
├── server.py              # Main application
└── environment.py         # Configuration
```

## Troubleshooting

**Port already in use:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000
# Kill the process (replace PID)
taskkill /PID <PID> /F
```

**LlamaParse authentication error:**
- Verify your API key is correct in `.env`
- Check your LlamaIndex Cloud account status
- Use `docling` engine as fallback (no API key required)

**File parsing fails:**
- Check file size (default limit: 50MB)
- Verify file format is supported
- Try the alternative parser engine

## License

MIT License - see LICENSE file for details.
