"""Search and retrieval endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from services.retriever_service import RetrieverService
from controllers.retriever_controller import RetrieverController
from models.requests import SearchRequest, SimilarDocumentsRequest
from models.responses import SearchResponse, SimilarDocumentsResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependencies to get services and controller
def get_retriever_service() -> RetrieverService:
    """Get retriever service instance."""
    try:
        return RetrieverService()
    except Exception as e:
        logger.error(f"Failed to initialize retriever service: {e}")
        raise HTTPException(status_code=503, detail="Retriever service not available")

def get_retriever_controller(
    retriever_service: RetrieverService = Depends(get_retriever_service)
) -> RetrieverController:
    """Get retriever controller instance."""
    return RetrieverController(retriever_service)


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    controller: RetrieverController = Depends(get_retriever_controller)
):
    """
    Perform semantic search across documents.
    
    Supports multiple search methods:
    - semantic: Pure vector similarity search
    - hybrid: Combination of semantic and keyword search
    - keyword: Text-based keyword matching
    """
    return controller.search(request)


@router.get("/search", response_model=SearchResponse)
async def search_documents_get(
    query: str = Query(..., description="Search query text"),
    collection_name: str = Query(..., description="Collection to search in"),
    method: str = Query("semantic", description="Search method: semantic, hybrid, or keyword"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    score_threshold: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score"),
    doc_ids: Optional[str] = Query(None, description="Comma-separated list of document IDs to filter"),
    rerank: bool = Query(True, description="Whether to apply reranking"),
    alpha: float = Query(0.7, ge=0.0, le=1.0, description="Weight for semantic vs keyword in hybrid mode"),
    controller: RetrieverController = Depends(get_retriever_controller)
):
    """
    Perform semantic search using GET method for simple queries.
    
    This endpoint provides a simpler interface for basic search operations.
    """
    # Parse doc_ids if provided
    parsed_doc_ids = None
    if doc_ids:
        parsed_doc_ids = [doc_id.strip() for doc_id in doc_ids.split(",") if doc_id.strip()]
    
    # Create search request
    search_request = SearchRequest(
        query=query,
        collection_name=collection_name,
        method=method,
        limit=limit,
        score_threshold=score_threshold,
        doc_ids=parsed_doc_ids,
        rerank=rerank,
        alpha=alpha
    )
    
    return controller.search(search_request)


@router.post("/similar", response_model=SimilarDocumentsResponse)
async def find_similar_documents(
    request: SimilarDocumentsRequest,
    controller: RetrieverController = Depends(get_retriever_controller)
):
    """
    Find documents similar to a given document.
    
    Uses the content of the specified document as a query to find
    semantically similar documents in the collection.
    """
    return controller.find_similar_documents(request)


@router.get("/similar/{collection_name}/{doc_id}", response_model=SimilarDocumentsResponse)
async def find_similar_documents_get(
    collection_name: str,
    doc_id: str,
    limit: int = Query(5, ge=1, le=50, description="Maximum number of similar documents"),
    controller: RetrieverController = Depends(get_retriever_controller)
):
    """
    Find similar documents using GET method.
    
    Simplified interface for finding documents similar to a specific document.
    """
    request = SimilarDocumentsRequest(
        doc_id=doc_id,
        collection_name=collection_name,
        limit=limit
    )
    
    return controller.find_similar_documents(request)


@router.get("/collections/{collection_name}/stats", response_model=dict)
async def get_collection_search_stats(
    collection_name: str,
    controller: RetrieverController = Depends(get_retriever_controller)
):
    """
    Get collection statistics for search optimization.
    
    Returns information about the collection that can help optimize
    search parameters and understand the data distribution.
    """
    return controller.get_collection_stats(collection_name)


@router.get("/methods", response_model=dict)
async def get_search_methods():
    """
    Get information about available search methods.
    
    Returns details about each search method and their use cases.
    """
    return {
        "methods": {
            "semantic": {
                "description": "Pure vector similarity search using embeddings",
                "use_case": "Best for finding conceptually similar content",
                "parameters": ["query", "collection_name", "limit", "score_threshold"]
            },
            "hybrid": {
                "description": "Combination of semantic and keyword search",
                "use_case": "Balanced approach for both semantic and exact matches",
                "parameters": ["query", "collection_name", "limit", "score_threshold", "alpha"]
            },
            "keyword": {
                "description": "Text-based keyword matching",
                "use_case": "Best for finding exact terms or phrases",
                "parameters": ["query", "collection_name", "limit"]
            }
        },
        "default_method": "semantic",
        "recommended_limits": {
            "min": 1,
            "max": 100,
            "default": 10
        },
        "score_threshold_range": {
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Higher values return only more similar results"
        }
    }


@router.get("/health", response_model=dict)
async def search_health_check(
    controller: RetrieverController = Depends(get_retriever_controller)
):
    """
    Health check for the search service.
    
    Verifies that the retriever service and its dependencies are working.
    """
    try:
        # Test basic functionality
        qdrant_healthy = controller.retriever_service.qdrant_service.health_check()
        
        return {
            "status": "healthy" if qdrant_healthy else "unhealthy",
            "retriever_service": "available",
            "qdrant_connection": "connected" if qdrant_healthy else "disconnected",
            "embedding_model": controller.retriever_service.settings.openai_embedding_model
        }
    except Exception as e:
        logger.error(f"Search health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
