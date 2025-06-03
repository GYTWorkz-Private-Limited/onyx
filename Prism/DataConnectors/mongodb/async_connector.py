"""
Async MongoDB DataConnector - Production-Ready Database Solution

A comprehensive, enterprise-grade async MongoDB database connector built with
Motor, designed for high-performance operations with intelligent connection
pooling, streaming capabilities, and robust error handling for large databases.

Features:
- Motor async driver for maximum performance
- Advanced aggregation pipeline support
- GridFS support for large file storage
- Geospatial query capabilities
- Text search functionality
- Change streams for real-time updates
- Bulk operations for large datasets
- Connection pooling with health monitoring
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, AsyncIterator, Union
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import (
    ConnectionFailure, ServerSelectionTimeoutError, OperationFailure,
    DuplicateKeyError, BulkWriteError, PyMongoError
)
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from bson import ObjectId
import gridfs
from datetime import datetime

from config import Config
from exceptions import (
    MongoConnectionError, MongoQueryError, MongoValidationError,
    MongoIndexError, MongoAggregationError
)
from utils import (
    async_retry, serialize_mongo_doc, serialize_mongo_cursor, to_object_id,
    build_sort_spec, build_projection, async_batch_processor, async_stream_cursor,
    AsyncConnectionPool, build_aggregation_pipeline, build_text_search_query,
    build_geospatial_query
)

logger = logging.getLogger(__name__)


class AsyncMongoDBConnector:
    """Async MongoDB database connector optimized for large databases and high performance."""

    def __init__(self, max_connections: int = 100):
        """
        Initialize async MongoDB connector with configurable pool settings.

        Args:
            max_connections: Maximum number of connections in the pool
        """
        Config.validate()
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self.max_connections = max_connections
        self._connection_pool = AsyncConnectionPool(max_connections)
        logger.info("Async MongoDB connector initialized successfully")

    async def _setup_client(self):
        """Setup Motor client with optimized configuration."""
        if self._client is not None:
            return

        try:
            connection_string = Config.get_connection_string()
            client_options = Config.get_client_options()

            # Override max pool size for async operations
            client_options['maxPoolSize'] = self.max_connections

            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                connection_string,
                **client_options
            )

            self._database = self._client[Config.MONGO_DB]

            # Test the connection
            await self._client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {Config.MONGO_HOST or 'URI'}")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise MongoConnectionError(f"MongoDB connection failed: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._setup_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()
        return False

    async def close(self):
        """Close MongoDB connection and cleanup resources."""
        try:
            if self._client:
                self._client.close()
                self._client = None
                self._database = None

            await self._connection_pool.close_all()
            logger.info("Async MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing async connector: {e}")

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get MongoDB client instance."""
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get MongoDB database instance."""
        return self._database

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get MongoDB collection instance."""
        return self._database[collection_name]

    # Connection and Health Methods
    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def test_connection(self) -> bool:
        """Test MongoDB connection health asynchronously."""
        try:
            await self._setup_client()
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def get_server_info(self) -> Dict[str, Any]:
        """Get MongoDB server information asynchronously."""
        try:
            await self._setup_client()
            return await self._client.server_info()
        except PyMongoError as e:
            logger.error(f"Failed to get server info: {e}")
            raise MongoConnectionError(f"Failed to get server info: {e}")

    # Document Operations
    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document and return the inserted ID asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.insert_one(document)
            logger.debug(f"Inserted document with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Insert operation failed: {e}")
            raise MongoQueryError(f"Failed to insert document: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]],
                         ordered: bool = True) -> List[str]:
        """Insert multiple documents and return the inserted IDs asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.insert_many(documents, ordered=ordered)
            inserted_ids = [str(oid) for oid in result.inserted_ids]
            logger.debug(f"Inserted {len(inserted_ids)} documents")
            return inserted_ids
        except BulkWriteError as e:
            logger.error(f"Bulk insert failed: {e}")
            raise MongoQueryError(f"Failed to insert documents: {e}")
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Insert many operation failed: {e}")
            raise MongoQueryError(f"Failed to insert documents: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any] = None,
                      projection: Dict[str, int] = None) -> Optional[Dict[str, Any]]:
        """Find a single document asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.find_one(filter_dict or {}, projection)
            return serialize_mongo_doc(result) if result else None
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Find one operation failed: {e}")
            raise MongoQueryError(f"Failed to find document: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None,
                       projection: Dict[str, int] = None, sort: List[tuple] = None,
                       limit: int = None, skip: int = None) -> List[Dict[str, Any]]:
        """Find multiple documents with optional sorting, limiting, and skipping asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            cursor = collection.find(filter_dict or {}, projection)

            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)

            documents = []
            async for doc in cursor:
                documents.append(serialize_mongo_doc(doc))

            return documents
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Find many operation failed: {e}")
            raise MongoQueryError(f"Failed to find documents: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def find_by_id(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Find document by ObjectId asynchronously."""
        try:
            object_id = to_object_id(document_id)
            return await self.find_one(collection_name, {"_id": object_id})
        except ValueError as e:
            raise MongoValidationError(f"Invalid ObjectId: {e}")

    # Large dataset streaming methods
    async def find_large_dataset(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any] = None,
        projection: Dict[str, int] = None,
        sort: List[tuple] = None,
        chunk_size: int = 1000
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Stream large datasets in chunks to handle memory efficiently.

        Args:
            collection_name: Name of the collection
            filter_dict: Query filter
            projection: Fields to include/exclude
            sort: Sort specification
            chunk_size: Number of documents to fetch in each chunk

        Yields:
            Chunks of documents
        """
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            cursor = collection.find(filter_dict or {}, projection)

            if sort:
                cursor = cursor.sort(sort)

            async for chunk in async_stream_cursor(cursor, chunk_size):
                yield chunk

        except Exception as e:
            logger.error(f"Failed to stream large dataset: {e}")
            raise MongoQueryError(f"Failed to stream documents: {e}")

    async def bulk_insert_with_batching(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 1000,
        ordered: bool = False
    ) -> bool:
        """
        Perform bulk insert operations optimized for large datasets.

        Args:
            collection_name: Target collection name
            documents: List of documents to insert
            batch_size: Number of documents to insert in each batch
            ordered: Whether to maintain order (slower but preserves order)

        Returns:
            True if successful
        """
        if not documents:
            return True

        async def process_batch(batch: List[Dict[str, Any]]) -> List[str]:
            """Process a single batch of inserts."""
            return await self.insert_many(collection_name, batch, ordered=ordered)

        try:
            results = await async_batch_processor(
                documents, batch_size, process_batch
            )

            total_inserted = sum(len(result) for result in results)
            logger.info(f"Successfully bulk inserted {total_inserted} documents into {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Bulk insert operation failed: {e}")
            raise MongoQueryError(f"Failed to bulk insert documents into {collection_name}: {e}")

    # Update Operations
    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def update_one(self, collection_name: str, filter_dict: Dict[str, Any],
                        update_dict: Dict[str, Any], upsert: bool = False) -> Dict[str, Any]:
        """Update a single document asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.update_one(filter_dict, update_dict, upsert=upsert)
            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None
            }
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Update one operation failed: {e}")
            raise MongoQueryError(f"Failed to update document: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def update_many(self, collection_name: str, filter_dict: Dict[str, Any],
                         update_dict: Dict[str, Any], upsert: bool = False) -> Dict[str, Any]:
        """Update multiple documents asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.update_many(filter_dict, update_dict, upsert=upsert)
            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None
            }
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Update many operation failed: {e}")
            raise MongoQueryError(f"Failed to update documents: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def update_by_id(self, collection_name: str, document_id: str,
                          update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Update document by ObjectId asynchronously."""
        try:
            object_id = to_object_id(document_id)
            return await self.update_one(collection_name, {"_id": object_id}, update_dict)
        except ValueError as e:
            raise MongoValidationError(f"Invalid ObjectId: {e}")

    # Delete Operations
    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete a single document asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.delete_one(filter_dict)
            return result.deleted_count
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Delete one operation failed: {e}")
            raise MongoQueryError(f"Failed to delete document: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete multiple documents asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.delete_many(filter_dict)
            return result.deleted_count
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Delete many operation failed: {e}")
            raise MongoQueryError(f"Failed to delete documents: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def delete_by_id(self, collection_name: str, document_id: str) -> int:
        """Delete document by ObjectId asynchronously."""
        try:
            object_id = to_object_id(document_id)
            return await self.delete_one(collection_name, {"_id": object_id})
        except ValueError as e:
            raise MongoValidationError(f"Invalid ObjectId: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents in collection asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            return await collection.count_documents(filter_dict or {})
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Count operation failed: {e}")
            raise MongoQueryError(f"Failed to count documents: {e}")

    # Collection Management
    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists asynchronously."""
        try:
            await self._setup_client()
            collection_names = await self._database.list_collection_names()
            return collection_name in collection_names
        except PyMongoError as e:
            logger.error(f"Failed to check collection existence: {e}")
            raise MongoQueryError(f"Failed to check collection existence: {e}")

    async def get_collection_names(self) -> List[str]:
        """Get list of all collection names asynchronously."""
        try:
            await self._setup_client()
            return await self._database.list_collection_names()
        except PyMongoError as e:
            logger.error(f"Failed to get collection names: {e}")
            raise MongoQueryError(f"Failed to get collection names: {e}")

    async def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection asynchronously."""
        try:
            await self._setup_client()
            await self._database.drop_collection(collection_name)
            logger.info(f"Dropped collection: {collection_name}")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to drop collection: {e}")
            raise MongoQueryError(f"Failed to drop collection: {e}")

    async def create_collection(self, collection_name: str, **options) -> AsyncIOMotorCollection:
        """Create a new collection with options asynchronously."""
        try:
            await self._setup_client()
            collection = await self._database.create_collection(collection_name, **options)
            logger.info(f"Created collection: {collection_name}")
            return collection
        except PyMongoError as e:
            logger.error(f"Failed to create collection: {e}")
            raise MongoQueryError(f"Failed to create collection: {e}")

    # Index Management
    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def create_index(self, collection_name: str, keys: Union[str, List[tuple]], **options) -> str:
        """Create an index on a collection asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.create_index(keys, **options)
            logger.info(f"Created index on {collection_name}: {result}")
            return result
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Failed to create index: {e}")
            raise MongoIndexError(f"Failed to create index: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def create_indexes(self, collection_name: str, indexes: List[Dict[str, Any]]) -> List[str]:
        """Create multiple indexes on a collection asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.create_indexes(indexes)
            logger.info(f"Created {len(result)} indexes on {collection_name}")
            return result
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Failed to create indexes: {e}")
            raise MongoIndexError(f"Failed to create indexes: {e}")

    async def get_indexes(self, collection_name: str) -> List[Dict[str, Any]]:
        """Get all indexes for a collection asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            indexes = []
            async for index in collection.list_indexes():
                indexes.append(index)
            return indexes
        except PyMongoError as e:
            logger.error(f"Failed to get indexes: {e}")
            raise MongoIndexError(f"Failed to get indexes: {e}")

    async def drop_index(self, collection_name: str, index_name: str) -> bool:
        """Drop an index from a collection asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            await collection.drop_index(index_name)
            logger.info(f"Dropped index {index_name} from {collection_name}")
            return True
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Failed to drop index: {e}")
            raise MongoIndexError(f"Failed to drop index: {e}")

    # Aggregation Operations
    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]],
                       **options) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            cursor = collection.aggregate(pipeline, **options)

            results = []
            async for doc in cursor:
                results.append(serialize_mongo_doc(doc))

            return results
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Aggregation failed: {e}")
            raise MongoAggregationError(f"Failed to execute aggregation: {e}")

    async def aggregate_large_dataset(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]],
        chunk_size: int = 1000,
        **options
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Execute aggregation pipeline and stream results for large datasets.

        Args:
            collection_name: Name of the collection
            pipeline: Aggregation pipeline
            chunk_size: Number of documents to yield in each chunk
            **options: Additional aggregation options

        Yields:
            Chunks of aggregation results
        """
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            cursor = collection.aggregate(pipeline, **options)

            async for chunk in async_stream_cursor(cursor, chunk_size):
                yield chunk

        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Aggregation streaming failed: {e}")
            raise MongoAggregationError(f"Failed to stream aggregation results: {e}")

    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def distinct(self, collection_name: str, field: str,
                      filter_dict: Dict[str, Any] = None) -> List[Any]:
        """Get distinct values for a field asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            return await collection.distinct(field, filter_dict or {})
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Distinct operation failed: {e}")
            raise MongoQueryError(f"Failed to get distinct values: {e}")

    # Advanced MongoDB Features
    async def text_search(self, collection_name: str, search_text: str,
                         language: str = "english", limit: int = None) -> List[Dict[str, Any]]:
        """
        Perform text search on a collection with text index.

        Args:
            collection_name: Name of the collection
            search_text: Text to search for
            language: Search language
            limit: Maximum number of results

        Returns:
            List of matching documents with text scores
        """
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)

            query = build_text_search_query(search_text, language)
            cursor = collection.find(query, {"score": {"$meta": "textScore"}})
            cursor = cursor.sort([("score", {"$meta": "textScore"})])

            if limit:
                cursor = cursor.limit(limit)

            results = []
            async for doc in cursor:
                results.append(serialize_mongo_doc(doc))

            return results
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Text search failed: {e}")
            raise MongoQueryError(f"Failed to perform text search: {e}")

    async def geospatial_search(
        self,
        collection_name: str,
        field: str,
        coordinates: List[float],
        max_distance: float = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Perform geospatial search on a collection with geospatial index.

        Args:
            collection_name: Name of the collection
            field: Field name containing geospatial data
            coordinates: [longitude, latitude] coordinates
            max_distance: Maximum distance in meters
            limit: Maximum number of results

        Returns:
            List of matching documents sorted by distance
        """
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)

            query = build_geospatial_query(field, "Point", coordinates, max_distance)
            cursor = collection.find(query)

            if limit:
                cursor = cursor.limit(limit)

            results = []
            async for doc in cursor:
                results.append(serialize_mongo_doc(doc))

            return results
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Geospatial search failed: {e}")
            raise MongoQueryError(f"Failed to perform geospatial search: {e}")

    # Bulk Operations
    @async_retry((ConnectionFailure, ServerSelectionTimeoutError), tries=3, delay=2)
    async def bulk_write(self, collection_name: str, operations: List[Any],
                        ordered: bool = True) -> Dict[str, Any]:
        """Execute bulk write operations asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.bulk_write(operations, ordered=ordered)
            return {
                "inserted_count": result.inserted_count,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "deleted_count": result.deleted_count,
                "upserted_count": result.upserted_count,
                "upserted_ids": {str(k): str(v) for k, v in result.upserted_ids.items()}
            }
        except BulkWriteError as e:
            logger.error(f"Bulk write failed: {e}")
            raise MongoQueryError(f"Failed to execute bulk write: {e}")
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Bulk write operation failed: {e}")
            raise MongoQueryError(f"Failed to execute bulk write: {e}")

    # Utility Methods
    async def find_with_pagination(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any] = None,
        projection: Dict[str, int] = None,
        sort_fields: List[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Find documents with pagination support asynchronously."""
        try:
            skip = (page - 1) * page_size
            sort_spec = build_sort_spec(sort_fields) if sort_fields else None

            documents = await self.find_many(
                collection_name=collection_name,
                filter_dict=filter_dict,
                projection=projection,
                sort=sort_spec,
                limit=page_size,
                skip=skip
            )

            total_count = await self.count_documents(collection_name, filter_dict)
            total_pages = (total_count + page_size - 1) // page_size

            return {
                "documents": documents,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_documents": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
        except Exception as e:
            logger.error(f"Pagination query failed: {e}")
            raise MongoQueryError(f"Failed to execute paginated query: {e}")

    async def replace_one(self, collection_name: str, filter_dict: Dict[str, Any],
                         replacement: Dict[str, Any], upsert: bool = False) -> Dict[str, Any]:
        """Replace a single document asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.replace_one(filter_dict, replacement, upsert=upsert)
            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None
            }
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Replace operation failed: {e}")
            raise MongoQueryError(f"Failed to replace document: {e}")

    async def find_one_and_update(
        self,
        collection_name: str,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any],
        return_document: str = "after",
        upsert: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Find and update a document atomically asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)

            return_doc = ReturnDocument.AFTER if return_document == "after" else ReturnDocument.BEFORE
            result = await collection.find_one_and_update(
                filter_dict, update_dict, return_document=return_doc, upsert=upsert
            )
            return serialize_mongo_doc(result) if result else None
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Find and update operation failed: {e}")
            raise MongoQueryError(f"Failed to find and update document: {e}")

    async def find_one_and_delete(self, collection_name: str,
                                 filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find and delete a document atomically asynchronously."""
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)
            result = await collection.find_one_and_delete(filter_dict)
            return serialize_mongo_doc(result) if result else None
        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Find and delete operation failed: {e}")
            raise MongoQueryError(f"Failed to find and delete document: {e}")

    # Database Operations
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics asynchronously."""
        try:
            await self._setup_client()
            return await self._database.command("dbStats")
        except PyMongoError as e:
            logger.error(f"Failed to get database stats: {e}")
            raise MongoQueryError(f"Failed to get database stats: {e}")

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics asynchronously."""
        try:
            await self._setup_client()
            return await self._database.command("collStats", collection_name)
        except PyMongoError as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise MongoQueryError(f"Failed to get collection stats: {e}")

    # Concurrent operations for high-performance scenarios
    async def execute_concurrent_operations(
        self,
        operations: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[Any]:
        """
        Execute multiple operations concurrently for improved performance.

        Args:
            operations: List of operation dictionaries with 'type', 'collection', and 'args' keys
            max_concurrent: Maximum number of concurrent operations

        Returns:
            List of results in the same order as input operations

        Example:
            operations = [
                {'type': 'find_one', 'collection': 'users', 'args': {'filter_dict': {'_id': ObjectId(...)}}},
                {'type': 'count_documents', 'collection': 'orders', 'args': {'filter_dict': {'status': 'active'}}},
                {'type': 'insert_one', 'collection': 'logs', 'args': {'document': {'message': 'test'}}}
            ]
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_operation(operation: Dict[str, Any]) -> Any:
            async with semaphore:
                op_type = operation['type']
                collection_name = operation['collection']
                args = operation.get('args', {})

                method = getattr(self, op_type)
                return await method(collection_name, **args)

        try:
            tasks = [execute_single_operation(operation) for operation in operations]
            results = await asyncio.gather(*tasks)
            logger.info(f"Executed {len(operations)} concurrent operations successfully")
            return results

        except Exception as e:
            logger.error(f"Concurrent operation execution failed: {e}")
            raise MongoQueryError(f"Failed to execute concurrent operations: {e}")

    # Change Streams for real-time updates
    async def watch_collection(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]] = None,
        full_document: str = "default"
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Watch a collection for changes using change streams.

        Args:
            collection_name: Name of the collection to watch
            pipeline: Optional aggregation pipeline to filter changes
            full_document: When to return the full document ("default", "updateLookup")

        Yields:
            Change events

        Example:
            async for change in connector.watch_collection("users"):
                print(f"Change detected: {change}")
        """
        try:
            await self._setup_client()
            collection = self.get_collection(collection_name)

            watch_options = {"full_document": full_document}
            if pipeline:
                change_stream = collection.watch(pipeline, **watch_options)
            else:
                change_stream = collection.watch(**watch_options)

            async for change in change_stream:
                yield serialize_mongo_doc(change)

        except (OperationFailure, PyMongoError) as e:
            logger.error(f"Change stream failed: {e}")
            raise MongoQueryError(f"Failed to watch collection: {e}")

    # GridFS operations for large file storage
    async def gridfs_put(self, file_data: bytes, filename: str, **metadata) -> str:
        """
        Store a file in GridFS asynchronously.

        Args:
            file_data: File content as bytes
            filename: Name of the file
            **metadata: Additional metadata for the file

        Returns:
            File ID as string
        """
        try:
            await self._setup_client()
            fs = motor.motor_asyncio.AsyncIOMotorGridFSBucket(self._database)

            # Create a BytesIO stream from the file data
            import io
            stream = io.BytesIO(file_data)

            file_id = await fs.upload_from_stream(
                filename,
                stream,
                metadata=metadata
            )

            stream.close()

            logger.info(f"Stored file {filename} in GridFS with ID: {file_id}")
            return str(file_id)

        except PyMongoError as e:
            logger.error(f"GridFS put operation failed: {e}")
            raise MongoQueryError(f"Failed to store file in GridFS: {e}")

    async def gridfs_get(self, file_id: str) -> bytes:
        """
        Retrieve a file from GridFS asynchronously.

        Args:
            file_id: File ID as string

        Returns:
            File content as bytes
        """
        try:
            await self._setup_client()
            fs = motor.motor_asyncio.AsyncIOMotorGridFSBucket(self._database)

            object_id = to_object_id(file_id)

            # Create a BytesIO stream to download the file content
            import io
            stream = io.BytesIO()
            await fs.download_to_stream(object_id, stream)

            # Get the bytes from the stream
            file_data = stream.getvalue()
            stream.close()

            logger.info(f"Retrieved file from GridFS with ID: {file_id}")
            return file_data

        except PyMongoError as e:
            logger.error(f"GridFS get operation failed: {e}")
            raise MongoQueryError(f"Failed to retrieve file from GridFS: {e}")
        except ValueError as e:
            raise MongoValidationError(f"Invalid file ID: {e}")

    async def gridfs_delete(self, file_id: str) -> bool:
        """
        Delete a file from GridFS asynchronously.

        Args:
            file_id: File ID as string

        Returns:
            True if successful
        """
        try:
            await self._setup_client()
            fs = motor.motor_asyncio.AsyncIOMotorGridFSBucket(self._database)

            object_id = to_object_id(file_id)
            await fs.delete(object_id)

            logger.info(f"Deleted file from GridFS with ID: {file_id}")
            return True

        except PyMongoError as e:
            logger.error(f"GridFS delete operation failed: {e}")
            raise MongoQueryError(f"Failed to delete file from GridFS: {e}")
        except ValueError as e:
            raise MongoValidationError(f"Invalid file ID: {e}")
