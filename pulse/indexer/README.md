# Document Indexing FastAPI Server

A FastAPI server for indexing documents into Qdrant vector database using OpenAI embeddings.

## Features

- **Document Indexing**: Index text files, uploaded files, or raw text content
- **Collection Management**: Create, delete, and manage Qdrant collections
- **File Upload**: Upload single or multiple files for indexing
- **Batch Processing**: Process directories of files or multiple text contents
- **RESTful API**: Full REST API with OpenAPI documentation
- **Configuration Management**: Environment-based configuration

## Quick Start

### Prerequisites

- Python 3.12+
- Docker (for Qdrant)
- OpenAI API key

### 1. Start Qdrant Database

```bash
docker-compose up -d
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Configure Environment

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Start the FastAPI Server

```bash
# Using Poetry
poetry run python main.py

# Or using uvicorn directly
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /` - API information

### Collections
- `GET /collections/` - List all collections
- `GET /collections/{name}` - Get collection information
- `POST /collections/{name}` - Create new collection
- `DELETE /collections/{name}` - Delete collection
- `PUT /collections/{name}/recreate` - Recreate collection

### File Management
- `POST /files/upload` - Upload single file
- `POST /files/upload-multiple` - Upload multiple files
- `GET /files/list` - List uploaded files
- `DELETE /files/{filename}` - Delete uploaded file

### Indexing
- `POST /index/file` - Index uploaded file
- `POST /index/files` - Index multiple uploaded files
- `POST /index/directory` - Index files from directory
- `POST /index/text` - Index raw text content
- `POST /index/batch` - Index multiple text contents

### Search & Retrieval
- `POST /search/search` - Semantic search with multiple methods
- `GET /search/search` - Simple search interface
- `POST /search/similar` - Find similar documents
- `GET /search/collections/{collection_name}/stats` - Collection statistics
- `GET /search/methods` - Available search methods

## Usage Examples

### Index the Campaign Finance Documents

```bash
# Create a collection
curl -X POST "http://localhost:8000/collections/campaign_finance" \
  -H "Content-Type: application/json" \
  -d '{}'

# Index the existing directory
curl -X POST "http://localhost:8000/index/directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./parsed_data_text",
    "collection_name": "campaign_finance",
    "file_extension": ".txt"
  }'
```

### Upload and Index a File

```bash
# Upload a file
curl -X POST "http://localhost:8000/files/upload" \
  -F "file=@your_document.txt"

# Index the uploaded file
curl -X POST "http://localhost:8000/index/file" \
  -F "file=@your_document.txt" \
  -F "collection_name=my_collection"
```

### Index Raw Text

```bash
curl -X POST "http://localhost:8000/index/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text content here...",
    "collection_name": "my_collection",
    "doc_id": "document_1"
  }'
```

## Detailed API Documentation

### Common Response Format

All indexing endpoints return an `IndexingResponse` object with the following structure:

```json
{
  "success": true,
  "message": "Operation description",
  "collection_name": "target_collection",
  "documents_processed": 5,
  "points_created": 15,
  "vectors_count": 150,
  "error": null
}
```

### Indexing Endpoints

#### 1. Index Single File Upload

**Endpoint:** `POST /index/file`

**Description:** Uploads and indexes a single text file into a Qdrant collection.

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (UploadFile, required): The text file to upload and index
- `collection_name` (str, required): Name of the Qdrant collection to index into
- `doc_id` (str, optional): Custom document identifier. If not provided, uses the filename

**Request Example:**
```bash
curl -X POST "http://localhost:8000/index/file" \
  -F "file=@document.txt" \
  -F "collection_name=my_documents" \
  -F "doc_id=doc_001"
```

**Response Example:**
```json
{
  "success": true,
  "message": "Successfully indexed file 'document.txt'",
  "collection_name": "my_documents",
  "documents_processed": 1,
  "points_created": 5,
  "vectors_count": 25,
  "error": null
}
```

#### 2. Index Multiple Files Upload

**Endpoint:** `POST /index/files`

**Description:** Uploads and indexes multiple text files into a Qdrant collection in a single operation.

**Content-Type:** `multipart/form-data`

**Parameters:**
- `files` (List[UploadFile], required): Multiple text files to upload and index
- `collection_name` (str, required): Name of the Qdrant collection to index into

**Request Example:**
```bash
curl -X POST "http://localhost:8000/index/files" \
  -F "files=@doc1.txt" \
  -F "files=@doc2.txt" \
  -F "files=@doc3.txt" \
  -F "collection_name=my_documents"
```

#### 3. Index Directory

**Endpoint:** `POST /index/directory`

**Description:** Indexes all files with a specified extension from a local directory.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "directory_path": "/path/to/documents",
  "collection_name": "my_documents",
  "file_extension": ".txt"
}
```

#### 4. Index Raw Text

**Endpoint:** `POST /index/text`

**Description:** Indexes raw text content directly without file upload.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "text": "This is the text content to be indexed...",
  "collection_name": "my_documents",
  "doc_id": "text_001"
}
```

#### 5. Batch Index Multiple Texts

**Endpoint:** `POST /index/batch`

**Description:** Indexes multiple text contents in a single batch operation for improved efficiency.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "texts": [
    "First document text content...",
    "Second document text content...",
    "Third document text content..."
  ],
  "collection_name": "my_documents",
  "doc_ids": [
    "doc_001",
    "doc_002",
    "doc_003"
  ]
}
```

### Search & Retrieval Endpoints

#### 1. Semantic Search

**Endpoint:** `POST /search/search`

**Description:** Perform semantic search using multiple methods (semantic, hybrid, keyword).

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "collection_name": "my_documents",
  "method": "semantic",
  "limit": 10,
  "score_threshold": 0.0,
  "doc_ids": ["doc1", "doc2"],
  "rerank": true,
  "alpha": 0.7
}
```

**Response Example:**
```json
{
  "success": true,
  "query": "machine learning algorithms",
  "collection_name": "my_documents",
  "method": "semantic",
  "total_results": 5,
  "results": [
    {
      "id": "uuid-123",
      "text": "Machine learning is a subset of artificial intelligence...",
      "doc_id": "doc1",
      "chunk_id": 0,
      "score": 0.95,
      "metadata": {}
    }
  ],
  "search_time_ms": 45.2
}
```

#### 2. Find Similar Documents

**Endpoint:** `POST /search/similar`

**Description:** Find documents similar to a given document.

**Request Body:**
```json
{
  "doc_id": "doc_001",
  "collection_name": "my_documents",
  "limit": 5
}
```

#### 3. Collection Search Statistics

**Endpoint:** `GET /search/collections/{collection_name}/stats`

**Description:** Get collection statistics for search optimization.

**Response Example:**
```json
{
  "collection_name": "my_documents",
  "total_vectors": 150,
  "indexed_vectors": 150,
  "unique_documents": 10,
  "total_chunks": 150,
  "average_chunk_length": 512.5,
  "search_ready": true
}
```

### Search Methods

#### Semantic Search
- **Method:** `semantic`
- **Description:** Pure vector similarity search using embeddings
- **Best for:** Finding conceptually similar content
- **Use case:** "Find documents about machine learning" → Returns docs about AI, neural networks, etc.

#### Hybrid Search
- **Method:** `hybrid`
- **Description:** Combines semantic and keyword search
- **Best for:** Balanced approach for both semantic and exact matches
- **Parameters:** `alpha` controls the weight (0.7 = 70% semantic, 30% keyword)
- **Use case:** "neural networks" → Returns both conceptually similar docs and exact phrase matches

#### Keyword Search
- **Method:** `keyword`
- **Description:** Text-based keyword matching
- **Best for:** Finding exact terms or phrases
- **Use case:** "API documentation" → Returns docs containing these exact words

## Configuration

The application can be configured using environment variables or the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `QDRANT_HOST` | `localhost` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `CHUNK_SIZE` | `512` | Text chunk size |
| `CHUNK_OVERLAP` | `100` | Text chunk overlap |
| `BATCH_SIZE` | `50` | Batch size for uploading |
| `MAX_FILE_SIZE` | `10485760` | Max file size (10MB) |
| `UPLOAD_DIRECTORY` | `uploads` | Upload directory |

## Project Structure

```
├── main.py                 # FastAPI application entry point
├── services/              # Core services
│   ├── config.py          # Configuration management
│   ├── indexing_service.py # Document indexing logic
│   └── qdrant_service.py   # Qdrant database operations
├── routers/               # API route handlers
│   ├── collections.py     # Collection management endpoints
│   ├── files.py           # File upload endpoints
│   └── indexing.py        # Document indexing endpoints
├── models/                # Pydantic models
│   ├── requests.py        # Request models
│   └── responses.py       # Response models
├── docker-compose.yml     # Qdrant database setup
├── .env                   # Environment configuration
└── README.md             # This file
```

## Development

### Code Quality

```bash
# Install development dependencies
pip install flake8 black isort

# Format code
black .
isort .

# Lint code
flake8 .
```

## Troubleshooting

### Common Issues

1. **Qdrant Connection Error**: Ensure Qdrant is running via Docker Compose
2. **OpenAI API Error**: Check your API key is valid and has sufficient credits
3. **File Upload Error**: Check file size limits and allowed extensions
4. **Memory Issues**: Reduce batch size for large documents

### Logs

The application logs to stdout. Increase log level for debugging:

```bash
export LOG_LEVEL=DEBUG
poetry run python main.py
```

## License

This project is licensed under the MIT License.
