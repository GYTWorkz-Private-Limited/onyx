"""Request models for the FastAPI application."""

from typing import Optional, List
from pydantic import BaseModel, Field


class IndexFileRequest(BaseModel):
    """Request model for indexing a single file."""
    collection_name: str = Field(..., description="Name of the collection to index into")
    doc_id: Optional[str] = Field(None, description="Custom document ID (defaults to filename)")


class IndexDirectoryRequest(BaseModel):
    """Request model for indexing files from a directory."""
    directory_path: str = Field(..., description="Path to the directory containing files")
    collection_name: str = Field(..., description="Name of the collection to index into")
    file_extension: str = Field(".txt", description="File extension to filter by")


class CreateCollectionRequest(BaseModel):
    """Request model for creating a new collection."""
    embedding_dimension: Optional[int] = Field(None, description="Embedding dimension (auto-detected if not provided)")


class IndexTextRequest(BaseModel):
    """Request model for indexing raw text content."""
    text: str = Field(..., description="Text content to index")
    collection_name: str = Field(..., description="Name of the collection to index into")
    doc_id: str = Field(..., description="Document identifier")


class BatchIndexRequest(BaseModel):
    """Request model for batch indexing multiple text contents."""
    texts: List[str] = Field(..., description="List of text contents to index")
    collection_name: str = Field(..., description="Name of the collection to index into")
    doc_ids: List[str] = Field(..., description="List of document identifiers")

    def validate_lengths(self):
        """Validate that texts and doc_ids have the same length."""
        if len(self.texts) != len(self.doc_ids):
            raise ValueError("texts and doc_ids must have the same length")


class SearchRequest(BaseModel):
    """Request model for semantic search operations."""
    query: str = Field(..., description="Search query text")
    collection_name: str = Field(..., description="Name of the collection to search in")
    method: str = Field("semantic", description="Search method: semantic, hybrid, or keyword")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    score_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity score threshold")
    doc_ids: Optional[List[str]] = Field(None, description="Filter results to specific document IDs")
    rerank: bool = Field(True, description="Whether to apply reranking to results")
    alpha: float = Field(0.7, ge=0.0, le=1.0, description="Weight for semantic vs keyword search in hybrid mode")


class SimilarDocumentsRequest(BaseModel):
    """Request model for finding similar documents."""
    doc_id: str = Field(..., description="Document ID to find similar documents for")
    collection_name: str = Field(..., description="Name of the collection to search in")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of similar documents to return")
