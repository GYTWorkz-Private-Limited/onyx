"""Controller for collection management operations."""

import logging
from typing import Dict, Any
from fastapi import HTTPException

from services.qdrant_service import QdrantService
from services.indexing_service import IndexingService
from models.requests import CreateCollectionRequest
from models.responses import CollectionInfo, CollectionListResponse

logger = logging.getLogger(__name__)


class CollectionsController:
    """Controller for coordinating collection management operations."""
    
    def __init__(self, qdrant_service: QdrantService, indexing_service: IndexingService):
        self.qdrant_service = qdrant_service
        self.indexing_service = indexing_service
    
    def list_collections(self) -> CollectionListResponse:
        """List all available collections."""
        try:
            collections = self.qdrant_service.list_collections()
            return CollectionListResponse(
                collections=collections,
                count=len(collections)
            )
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_collection_info(self, collection_name: str) -> CollectionInfo:
        """Get detailed information about a specific collection."""
        try:
            if not self.qdrant_service.collection_exists(collection_name):
                raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
            
            collection_info = self.qdrant_service.get_collection_info(collection_name)
            if not collection_info:
                raise HTTPException(status_code=500, detail="Failed to retrieve collection information")
            
            return CollectionInfo(
                name=collection_name,
                vectors_count=collection_info.vectors_count,
                indexed_vectors_count=collection_info.indexed_vectors_count,
                points_count=collection_info.points_count,
                segments_count=collection_info.segments_count,
                config=collection_info.config.model_dump() if collection_info.config else {}
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def create_collection(self, collection_name: str, request: CreateCollectionRequest) -> Dict[str, Any]:
        """Create a new collection with specified or auto-detected embedding dimension."""
        try:
            # Get embedding dimension
            embedding_dim = request.embedding_dimension
            if not embedding_dim:
                embedding_dim = self.indexing_service.get_embedding_dimension()
            
            # Create collection
            success = self.qdrant_service.create_collection(collection_name, embedding_dim)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to create collection")
            
            return {
                "message": f"Collection '{collection_name}' created successfully",
                "collection_name": collection_name,
                "embedding_dimension": embedding_dim
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete an existing collection."""
        try:
            if not self.qdrant_service.collection_exists(collection_name):
                raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
            
            success = self.qdrant_service.delete_collection(collection_name)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete collection")
            
            return {
                "message": f"Collection '{collection_name}' deleted successfully",
                "collection_name": collection_name
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def recreate_collection(self, collection_name: str, request: CreateCollectionRequest) -> Dict[str, Any]:
        """Recreate a collection (delete existing and create new)."""
        try:
            # Get embedding dimension
            embedding_dim = request.embedding_dimension
            if not embedding_dim:
                embedding_dim = self.indexing_service.get_embedding_dimension()
            
            # Recreate collection (create_collection handles deletion if exists)
            success = self.qdrant_service.create_collection(collection_name, embedding_dim)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to recreate collection")
            
            return {
                "message": f"Collection '{collection_name}' recreated successfully",
                "collection_name": collection_name,
                "embedding_dimension": embedding_dim
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error recreating collection {collection_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
