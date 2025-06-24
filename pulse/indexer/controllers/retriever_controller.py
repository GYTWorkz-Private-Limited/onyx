"""Controller for retriever and search operations."""

import logging
import time
from typing import List
from fastapi import HTTPException

from services.retriever_service import RetrieverService, SearchParams, SearchMethod
from models.requests import SearchRequest, SimilarDocumentsRequest
from models.responses import SearchResponse, SimilarDocumentsResponse, SearchResultItem

logger = logging.getLogger(__name__)


class RetrieverController:
    """Controller for coordinating search and retrieval operations."""
    
    def __init__(self, retriever_service: RetrieverService):
        self.retriever_service = retriever_service
    
    def search(self, request: SearchRequest) -> SearchResponse:
        """Perform semantic search with various methods."""
        start_time = time.time()
        
        try:
            # Validate search method
            try:
                search_method = SearchMethod(request.method.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid search method: {request.method}. Must be one of: semantic, hybrid, keyword"
                )
            
            # Create search parameters
            search_params = SearchParams(
                method=search_method,
                limit=request.limit,
                score_threshold=request.score_threshold,
                doc_ids=request.doc_ids,
                rerank=request.rerank,
                alpha=request.alpha
            )
            
            # Perform search
            results = self.retriever_service.search(
                query=request.query,
                collection_name=request.collection_name,
                params=search_params
            )
            
            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000
            
            # Convert results to response format
            result_items = [
                SearchResultItem(
                    id=result.id,
                    text=result.text,
                    doc_id=result.doc_id,
                    chunk_id=result.chunk_id,
                    score=result.score,
                    metadata=result.metadata
                )
                for result in results
            ]
            
            return SearchResponse(
                success=True,
                query=request.query,
                collection_name=request.collection_name,
                method=request.method,
                total_results=len(result_items),
                results=result_items,
                search_time_ms=search_time_ms
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during search: {e}")
            search_time_ms = (time.time() - start_time) * 1000
            
            return SearchResponse(
                success=False,
                query=request.query,
                collection_name=request.collection_name,
                method=request.method,
                total_results=0,
                results=[],
                search_time_ms=search_time_ms,
                error=str(e)
            )
    
    def find_similar_documents(self, request: SimilarDocumentsRequest) -> SimilarDocumentsResponse:
        """Find documents similar to a given document."""
        try:
            # Perform similar document search
            results = self.retriever_service.get_similar_documents(
                doc_id=request.doc_id,
                collection_name=request.collection_name,
                limit=request.limit
            )
            
            # Convert results to response format
            result_items = [
                SearchResultItem(
                    id=result.id,
                    text=result.text,
                    doc_id=result.doc_id,
                    chunk_id=result.chunk_id,
                    score=result.score,
                    metadata=result.metadata
                )
                for result in results
            ]
            
            return SimilarDocumentsResponse(
                success=True,
                doc_id=request.doc_id,
                collection_name=request.collection_name,
                total_results=len(result_items),
                results=result_items
            )
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            
            return SimilarDocumentsResponse(
                success=False,
                doc_id=request.doc_id,
                collection_name=request.collection_name,
                total_results=0,
                results=[],
                error=str(e)
            )
    
    def search_by_text(
        self, 
        query: str, 
        collection_name: str, 
        method: str = "semantic",
        limit: int = 10,
        score_threshold: float = 0.0
    ) -> SearchResponse:
        """Simple search interface for direct text queries."""
        request = SearchRequest(
            query=query,
            collection_name=collection_name,
            method=method,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return self.search(request)
    
    def get_collection_stats(self, collection_name: str) -> dict:
        """Get statistics about a collection for search optimization."""
        try:
            # Check if collection exists
            if not self.retriever_service.qdrant_service.collection_exists(collection_name):
                raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
            
            # Get collection info
            collection_info = self.retriever_service.qdrant_service.get_collection_info(collection_name)
            
            if not collection_info:
                raise HTTPException(status_code=500, detail="Failed to retrieve collection information")
            
            # Get sample documents to analyze
            scroll_result = self.retriever_service.qdrant_service.client.scroll(
                collection_name=collection_name,
                limit=100,
                with_payload=True
            )
            
            # Analyze document statistics
            doc_ids = set()
            total_chunks = 0
            text_lengths = []
            
            for point in scroll_result[0]:
                doc_ids.add(point.payload.get("doc_id", ""))
                total_chunks += 1
                text_lengths.append(len(point.payload.get("text", "")))
            
            avg_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
            
            return {
                "collection_name": collection_name,
                "total_vectors": collection_info.vectors_count,
                "indexed_vectors": collection_info.indexed_vectors_count,
                "total_points": collection_info.points_count,
                "unique_documents": len(doc_ids),
                "total_chunks": total_chunks,
                "average_chunk_length": round(avg_text_length, 2),
                "segments_count": collection_info.segments_count,
                "search_ready": collection_info.indexed_vectors_count > 0
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
