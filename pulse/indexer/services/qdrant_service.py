"""Qdrant vector database service."""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, TextIndexParams, TokenizerType, 
    OptimizersConfigDiff, PointStruct, CollectionInfo
)
from qdrant_client.http.exceptions import ResponseHandlingException

from .config import get_settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for managing Qdrant vector database operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Qdrant database."""
        try:
            self.client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                timeout=self.settings.qdrant_timeout
            )
            logger.info(f"Connected to Qdrant at {self.settings.qdrant_host}:{self.settings.qdrant_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        try:
            return self.client.collection_exists(collection_name)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def create_collection(self, collection_name: str, embedding_size: int) -> bool:
        """Create a new collection with text indexing."""
        try:
            # Delete existing collection if it exists
            if self.collection_exists(collection_name):
                self.client.delete_collection(collection_name)
                logger.info(f"Deleted existing collection: {collection_name}")
            
            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE),
                optimizers_config=OptimizersConfigDiff(
                    indexing_threshold=100  # Lower threshold for faster indexing
                )
            )
            
            # Add full-text index on text field
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="text",
                field_schema=TextIndexParams(
                    type="text",
                    tokenizer=TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=15,
                    lowercase=True
                )
            )
            
            logger.info(f"Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            if self.collection_exists(collection_name):
                self.client.delete_collection(collection_name)
                logger.info(f"Deleted collection: {collection_name}")
                return True
            else:
                logger.warning(f"Collection {collection_name} does not exist")
                return False
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[CollectionInfo]:
        """Get collection information."""
        try:
            if self.collection_exists(collection_name):
                return self.client.get_collection(collection_name)
            return None
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return None
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def upsert_points(self, collection_name: str, points: List[PointStruct]) -> bool:
        """Upload points to collection in batches."""
        try:
            batch_size = self.settings.batch_size
            total_batches = (len(points) + batch_size - 1) // batch_size
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                batch_num = i // batch_size + 1
                logger.info(f"Uploaded batch {batch_num}/{total_batches} ({len(batch)} points)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error uploading points to {collection_name}: {e}")
            return False
