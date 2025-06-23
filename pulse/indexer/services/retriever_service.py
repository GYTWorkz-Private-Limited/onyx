"""Retriever service for semantic search operations."""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from qdrant_client.http.models import Filter, FieldCondition, MatchValue, SearchRequest
from llama_index.embeddings.openai import OpenAIEmbedding

from .config import get_settings
from .qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class SearchMethod(Enum):
    """Available search methods."""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"


@dataclass
class SearchResult:
    """Search result data structure."""
    id: str
    text: str
    doc_id: str
    chunk_id: int
    score: float
    metadata: Dict[str, Any] = None


@dataclass
class SearchParams:
    """Search parameters configuration."""
    method: SearchMethod = SearchMethod.SEMANTIC
    limit: int = 10
    score_threshold: float = 0.0
    doc_ids: Optional[List[str]] = None
    rerank: bool = True
    alpha: float = 0.7  # Weight for semantic vs keyword search in hybrid mode


class RetrieverService:
    """Service for semantic search and document retrieval."""
    
    def __init__(self):
        self.settings = get_settings()
        self.qdrant_service = QdrantService()
        self.embed_model = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the retriever service."""
        try:
            # Initialize embedding model (same as indexing service)
            self.embed_model = OpenAIEmbedding(model=self.settings.openai_embedding_model)
            logger.info("Retriever service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize retriever service: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        collection_name: str, 
        params: Optional[SearchParams] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search with multiple methods.
        
        Args:
            query: Search query text
            collection_name: Target collection name
            params: Search parameters
            
        Returns:
            List of search results
        """
        if params is None:
            params = SearchParams()
        
        try:
            # Check if collection exists
            if not self.qdrant_service.collection_exists(collection_name):
                raise ValueError(f"Collection '{collection_name}' does not exist")
            
            # Route to appropriate search method
            if params.method == SearchMethod.SEMANTIC:
                results = self._semantic_search(query, collection_name, params)
            elif params.method == SearchMethod.HYBRID:
                results = self._hybrid_search(query, collection_name, params)
            elif params.method == SearchMethod.KEYWORD:
                results = self._keyword_search(query, collection_name, params)
            else:
                raise ValueError(f"Unsupported search method: {params.method}")
            
            # Apply post-processing
            results = self._post_process_results(results, params)
            
            logger.info(f"Search completed: {len(results)} results for query '{query[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise
    
    def _semantic_search(
        self, 
        query: str, 
        collection_name: str, 
        params: SearchParams
    ) -> List[SearchResult]:
        """Perform pure semantic vector search."""
        try:
            # Generate query embedding
            query_embedding = self.embed_model.get_text_embedding(query)
            
            # Build search filter
            search_filter = self._build_filter(params)
            
            # Perform vector search
            search_results = self.qdrant_service.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=params.limit * 2,  # Get more results for potential reranking
                score_threshold=params.score_threshold,
                query_filter=search_filter,
                with_payload=True
            )
            
            # Convert to SearchResult objects
            results = []
            for result in search_results:
                results.append(SearchResult(
                    id=str(result.id),
                    text=result.payload.get("text", ""),
                    doc_id=result.payload.get("doc_id", ""),
                    chunk_id=result.payload.get("chunk_id", 0),
                    score=result.score,
                    metadata=result.payload
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise
    
    def _hybrid_search(
        self, 
        query: str, 
        collection_name: str, 
        params: SearchParams
    ) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword search."""
        try:
            # Get semantic search results
            semantic_params = SearchParams(
                method=SearchMethod.SEMANTIC,
                limit=params.limit,
                score_threshold=params.score_threshold,
                doc_ids=params.doc_ids,
                rerank=False  # We'll rerank after combining
            )
            semantic_results = self._semantic_search(query, collection_name, semantic_params)
            
            # Get keyword search results
            keyword_params = SearchParams(
                method=SearchMethod.KEYWORD,
                limit=params.limit,
                doc_ids=params.doc_ids,
                rerank=False
            )
            keyword_results = self._keyword_search(query, collection_name, keyword_params)
            
            # Combine and rerank results
            combined_results = self._combine_search_results(
                semantic_results, 
                keyword_results, 
                params.alpha
            )
            
            return combined_results[:params.limit]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise
    
    def _keyword_search(
        self, 
        query: str, 
        collection_name: str, 
        params: SearchParams
    ) -> List[SearchResult]:
        """Perform keyword-based search using full-text search."""
        try:
            # Build search filter
            search_filter = self._build_filter(params)
            
            # Perform scroll search with text matching
            # Note: This is a simplified keyword search
            # For production, you might want to use more sophisticated text matching
            scroll_result = self.qdrant_service.client.scroll(
                collection_name=collection_name,
                scroll_filter=search_filter,
                limit=params.limit * 3,  # Get more for keyword matching
                with_payload=True
            )
            
            # Filter results based on keyword matching
            query_terms = query.lower().split()
            results = []
            
            for point in scroll_result[0]:  # scroll_result is (points, next_page_offset)
                text = point.payload.get("text", "").lower()
                
                # Simple keyword matching score
                score = self._calculate_keyword_score(text, query_terms)
                
                if score > 0:
                    results.append(SearchResult(
                        id=str(point.id),
                        text=point.payload.get("text", ""),
                        doc_id=point.payload.get("doc_id", ""),
                        chunk_id=point.payload.get("chunk_id", 0),
                        score=score,
                        metadata=point.payload
                    ))
            
            # Sort by score and return top results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:params.limit]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            raise
    
    def _build_filter(self, params: SearchParams) -> Optional[Filter]:
        """Build Qdrant filter from search parameters."""
        if not params.doc_ids:
            return None
        
        return Filter(
            must=[
                FieldCondition(
                    key="doc_id",
                    match=MatchValue(value=doc_id)
                ) for doc_id in params.doc_ids
            ]
        )
    
    def _calculate_keyword_score(self, text: str, query_terms: List[str]) -> float:
        """Calculate keyword matching score."""
        if not query_terms:
            return 0.0
        
        matches = 0
        for term in query_terms:
            if term in text:
                matches += 1
        
        return matches / len(query_terms)
    
    def _combine_search_results(
        self, 
        semantic_results: List[SearchResult], 
        keyword_results: List[SearchResult], 
        alpha: float
    ) -> List[SearchResult]:
        """Combine semantic and keyword search results with weighted scoring."""
        # Create a map of all unique results
        result_map = {}
        
        # Add semantic results
        for result in semantic_results:
            result_map[result.id] = result
            result.score = alpha * result.score  # Weight semantic score
        
        # Add/update with keyword results
        for result in keyword_results:
            if result.id in result_map:
                # Combine scores
                existing = result_map[result.id]
                existing.score += (1 - alpha) * result.score
            else:
                # New result from keyword search
                result.score = (1 - alpha) * result.score
                result_map[result.id] = result
        
        # Convert back to list and sort
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        return combined_results
    
    def _post_process_results(
        self, 
        results: List[SearchResult], 
        params: SearchParams
    ) -> List[SearchResult]:
        """Apply post-processing to search results."""
        if not results:
            return results
        
        # Apply reranking if requested
        if params.rerank:
            results = self._rerank_results(results)
        
        # Apply final limit
        return results[:params.limit]
    
    def _rerank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Rerank results using additional criteria."""
        # Simple reranking based on text length and score
        # In production, you might use more sophisticated reranking models
        
        for result in results:
            # Boost score for results with reasonable text length
            text_length = len(result.text)
            if 100 <= text_length <= 1000:  # Optimal length range
                result.score *= 1.1
            elif text_length < 50:  # Too short
                result.score *= 0.9
        
        # Sort by updated scores
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def get_similar_documents(
        self, 
        doc_id: str, 
        collection_name: str, 
        limit: int = 5
    ) -> List[SearchResult]:
        """Find documents similar to a given document."""
        try:
            # First, get the document content
            scroll_result = self.qdrant_service.client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                ),
                limit=1,
                with_payload=True
            )
            
            if not scroll_result[0]:
                raise ValueError(f"Document with id '{doc_id}' not found")
            
            # Use the document text as query for similarity search
            doc_text = scroll_result[0][0].payload.get("text", "")
            
            # Perform semantic search excluding the original document
            params = SearchParams(
                method=SearchMethod.SEMANTIC,
                limit=limit + 5,  # Get extra to filter out original
                score_threshold=0.1
            )
            
            results = self._semantic_search(doc_text, collection_name, params)
            
            # Filter out the original document
            filtered_results = [r for r in results if r.doc_id != doc_id]
            
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            raise
