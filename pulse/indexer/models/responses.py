"""Response models for the FastAPI application."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.now)
    qdrant_connected: bool = Field(..., description="Whether Qdrant is connected")


class CollectionInfo(BaseModel):
    """Collection information response."""
    name: str = Field(..., description="Collection name")
    vectors_count: Optional[int] = Field(None, description="Number of vectors in collection")
    indexed_vectors_count: Optional[int] = Field(None, description="Number of indexed vectors")
    points_count: Optional[int] = Field(None, description="Number of points in collection")
    segments_count: Optional[int] = Field(None, description="Number of segments")
    config: Dict[str, Any] = Field(default_factory=dict, description="Collection configuration")


class CollectionListResponse(BaseModel):
    """Response for listing collections."""
    collections: List[str] = Field(..., description="List of collection names")
    count: int = Field(..., description="Number of collections")


class IndexingResponse(BaseModel):
    """Response for indexing operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    collection_name: str = Field(..., description="Name of the collection")
    documents_processed: int = Field(..., description="Number of documents processed")
    points_created: Optional[int] = Field(None, description="Number of points created")
    vectors_count: Optional[int] = Field(None, description="Total vectors in collection after operation")
    job_id: Optional[str] = Field(None, description="Job ID for async operations")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class JobStatus(BaseModel):
    """Job status response."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status (pending, running, completed, failed)")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[IndexingResponse] = Field(None, description="Job result if completed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    error: Optional[str] = Field(None, description="Error message if job failed")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now)


class FileUploadResponse(BaseModel):
    """File upload response."""
    filename: str = Field(..., description="Uploaded filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File content type")
    saved_path: str = Field(..., description="Path where file was saved")


class SearchResultItem(BaseModel):
    """Individual search result item."""
    id: str = Field(..., description="Unique identifier of the result")
    text: str = Field(..., description="Text content of the result")
    doc_id: str = Field(..., description="Document ID this result belongs to")
    chunk_id: int = Field(..., description="Chunk ID within the document")
    score: float = Field(..., description="Similarity score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchResponse(BaseModel):
    """Response for search operations."""
    success: bool = Field(..., description="Whether the search was successful")
    query: str = Field(..., description="Original search query")
    collection_name: str = Field(..., description="Collection that was searched")
    method: str = Field(..., description="Search method used")
    total_results: int = Field(..., description="Total number of results found")
    results: List[SearchResultItem] = Field(..., description="List of search results")
    search_time_ms: Optional[float] = Field(None, description="Search execution time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if search failed")


class SimilarDocumentsResponse(BaseModel):
    """Response for similar documents search."""
    success: bool = Field(..., description="Whether the search was successful")
    doc_id: str = Field(..., description="Original document ID")
    collection_name: str = Field(..., description="Collection that was searched")
    total_results: int = Field(..., description="Total number of similar documents found")
    results: List[SearchResultItem] = Field(..., description="List of similar documents")
    error: Optional[str] = Field(None, description="Error message if search failed")
