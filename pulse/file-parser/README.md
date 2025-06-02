# 📄 File Parser API (Docling & LLaMAParse)

A modular, production-ready FastAPI service that parses uploaded documents using either **Docling** or **LlamaParse**, returning both **plain text** and **Markdown** formats.

---

## ✅ Features

- **Modular Architecture**: Clean separation of concerns with organized folder structure
- **Multiple Parser Engines**: Choose between `docling` (open-source) or `llama` (cloud-based)
- **Wide Format Support**: `.pdf`, `.docx`, `.csv`, `.xlsx`, `.pptx`
- **Dual Output**: Plain text (`.txt`) and Markdown (`.md`) formats
- **RESTful API**: Well-documented endpoints with OpenAPI/Swagger
- **Type Safety**: Full Pydantic schema validation
- **Error Handling**: Comprehensive error handling and validation
- **Environment Configuration**: Flexible configuration via environment variables

---

## 🏗️ Project Structure

```
file-parser/
├── api/                    # API routes and endpoints
│   ├── __init__.py
│   └── parse_routes.py     # Parse endpoint routes
├── controllers/            # Business logic controllers
│   ├── __init__.py
│   └── parse_controller.py # Parse operations controller
├── models/                 # Data models and schemas
│   ├── __init__.py
│   └── parse_models.py     # Parse result models
├── services/               # Core parsing services
│   ├── __init__.py
│   ├── base_parser.py      # Abstract base parser
│   ├── docling_service.py  # Docling parsing service
│   └── llamaparse_service.py # LlamaParse service
├── schemas/                # Pydantic schemas
│   ├── __init__.py
│   └── parse_schemas.py    # Request/response schemas
├── utils/                  # General utilities
│   ├── __init__.py
│   ├── constants.py        # Application constants
│   ├── file_validator.py   # File validation utilities
│   ├── logging_config.py   # Logging configuration
│   └── output_writer.py    # Output writing utilities
├── output/                 # Generated output files
├── temp/                   # Temporary files (auto-created)
├── logs/                   # Application logs
├── environment.py          # Environment configuration
├── server.py              # FastAPI application setup
├── pyproject.toml         # Poetry project configuration
├── poetry.lock           # Poetry lock file (auto-generated)
└── README.md             # This file
```

---

## 🛠 Setup

### 1. Clone and Navigate

```bash
git clone <your-repo-url>
cd file-parser
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

**Using Poetry (recommended)**
```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

**Alternative: Using pip with pyproject.toml**
```bash
pip install -e .
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# LlamaParse Configuration
LLAMA_CLOUD_API_KEY=llx-<your-key>
PARSER_MODE=balanced
OUTPUT_FORMAT=markdown

# Application Configuration
OUTPUT_DIR=output
TEMP_DIR=temp
HOST=0.0.0.0
PORT=8000
DEBUG=false

# File Processing
MAX_FILE_SIZE=50000000
```

---

## 🚀 Running the Application

### Development Mode

```bash
poetry run uvicorn server:app --reload
```

### Production Mode

```bash
poetry run uvicorn server:app --host 0.0.0.0 --port 8000
```

### Using Python directly

```bash
poetry run python server.py
```

### Using Makefile

```bash
make run          # Development mode
make run-prod     # Production mode
```

Open your browser at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📚 API Documentation

### Endpoints

- **POST `/api/v1/parse/`** - Parse uploaded file
- **GET `/api/v1/engines/`** - Get supported parser engines
- **GET `/api/v1/health/`** - Health check
- **GET `/docs`** - Interactive API documentation
- **GET `/redoc`** - Alternative API documentation

### Example Usage

```bash
# Using curl (Linux/Mac)
curl -X POST "http://localhost:8000/api/v1/parse/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf" \
     -F "engine=llama"

# Using PowerShell (Windows)
$form = @{
    file = Get-Item "document.pdf"
    engine = "llama"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/parse/" -Method Post -Form $form
```

---

## 📂 Output Structure

For a file named `invoice.pdf`, you'll get:

```
output/
├── invoice.txt      # Plain text extraction
└── invoice.md       # Markdown formatted extraction
```

---

## 🔧 Development

### Code Quality Tools

```bash
# Install development dependencies
poetry install

# Format code
make format
# or directly: poetry run black . && poetry run isort .

# Lint code
make lint
# or directly: poetry run flake8 . && poetry run mypy .

# Run tests
make test
# or directly: poetry run pytest tests/ -v

# Run tests with coverage
make test-coverage
# or directly: poetry run pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Check everything
make check
```

### Adding New Parser Engines

1. Create a new service in `services/` inheriting from `BaseParser`
2. Implement the required abstract methods
3. Add the engine to `ParserEngine` enum in `schemas/parse_schemas.py`
4. Update the controller to handle the new engine

---

## 📝 License

MIT License - see LICENSE file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📞 Support

For issues and questions, please open an issue on GitHub.
