"""
Async MongoDB DataConnector Package

A comprehensive, enterprise-grade asynchronous MongoDB connector built with Motor,
designed for high-performance applications with intelligent connection pooling,
advanced aggregation support, and robust error handling optimized for large databases.

Features:
- Asynchronous connection support with Motor
- Connection pooling with configurable pool sizes
- Advanced aggregation pipeline support
- GridFS support for large file storage
- Text search and geospatial queries
- Change streams for real-time updates
- Bulk operations with batching for large datasets
- Comprehensive error handling with custom exceptions
- Environment-based configuration management
- Full type safety with type hints
- MongoDB-specific features (ObjectId, BSON, etc.)

Author: Augment Agent
Version: 2.0.0
"""

from .async_connector import AsyncMongoDBConnector
from .config import Config
from .exceptions import (
    MongoConnectionError,
    MongoQueryError,
    MongoValidationError,
    MongoIndexError,
    MongoAggregationError
)
from .utils import (
    serialize_mongo_doc, to_object_id, build_sort_spec, build_projection,
    async_retry, async_batch_processor, build_aggregation_pipeline,
    build_text_search_query, build_geospatial_query
)

__version__ = "2.0.0"
__author__ = "Augment Agent"
__email__ = "support@augmentcode.com"

__all__ = [
    # Core async connector
    "AsyncMongoDBConnector",
    "Config",

    # Exceptions
    "MongoConnectionError",
    "MongoQueryError",
    "MongoValidationError",
    "MongoIndexError",
    "MongoAggregationError",

    # Async utilities
    "serialize_mongo_doc",
    "to_object_id",
    "build_sort_spec",
    "build_projection",
    "async_retry",
    "async_batch_processor",
    "build_aggregation_pipeline",
    "build_text_search_query",
    "build_geospatial_query",
]
