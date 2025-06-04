import asyncio
from functools import wraps
from typing import Any, Dict, List, AsyncIterator, Optional
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None

    serialized = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_mongo_doc(value)
        elif isinstance(value, list):
            serialized[key] = [serialize_mongo_doc(item) if isinstance(item, dict) else item for item in value]
        else:
            serialized[key] = value

    return serialized

def serialize_mongo_cursor(cursor) -> List[Dict[str, Any]]:
    """Convert MongoDB cursor to list of JSON-serializable documents"""
    return [serialize_mongo_doc(doc) for doc in cursor]

def validate_object_id(oid: str) -> bool:
    """Validate if string is a valid MongoDB ObjectId"""
    try:
        ObjectId(oid)
        return True
    except:
        return False

def to_object_id(oid: str) -> ObjectId:
    """Convert string to ObjectId with validation"""
    if not validate_object_id(oid):
        raise ValueError(f"Invalid ObjectId: {oid}")
    return ObjectId(oid)

def build_sort_spec(sort_fields: List[str]) -> List[tuple]:
    """Build MongoDB sort specification from field list

    Args:
        sort_fields: List of field names, prefix with '-' for descending order

    Returns:
        List of (field, direction) tuples for MongoDB sort
    """
    sort_spec = []
    for field in sort_fields:
        if field.startswith('-'):
            sort_spec.append((field[1:], -1))  # Descending
        else:
            sort_spec.append((field, 1))  # Ascending
    return sort_spec

def build_projection(include_fields: List[str] = None, exclude_fields: List[str] = None) -> Dict[str, int]:
    """Build MongoDB projection specification

    Args:
        include_fields: Fields to include in result
        exclude_fields: Fields to exclude from result

    Returns:
        MongoDB projection dictionary
    """
    projection = {}

    if include_fields:
        for field in include_fields:
            projection[field] = 1

    if exclude_fields:
        for field in exclude_fields:
            projection[field] = 0

    return projection if projection else None


def async_retry(exceptions, tries=3, delay=1):
    """Async retry decorator for handling transient MongoDB errors"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < tries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt == tries:
                        raise
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


async def async_batch_processor(
    items: List[Any],
    batch_size: int,
    processor_func,
    *args,
    **kwargs
) -> List[Any]:
    """
    Process items in batches asynchronously for large dataset operations.

    Args:
        items: List of items to process
        batch_size: Number of items to process in each batch
        processor_func: Async function to process each batch
        *args, **kwargs: Additional arguments for processor_func

    Returns:
        List of results from all batches

    Example:
        async def process_batch(batch, collection):
            return await collection.insert_many(batch)

        results = await async_batch_processor(
            large_dataset, 1000, process_batch, collection
        )
    """
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        try:
            result = await processor_func(batch, *args, **kwargs)
            results.append(result)
            logger.debug(f"Processed batch {i//batch_size + 1} ({len(batch)} items)")
        except Exception as e:
            logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
            raise
    return results


async def async_stream_cursor(
    cursor,
    chunk_size: int = 1000
) -> AsyncIterator[List[Dict[str, Any]]]:
    """
    Stream MongoDB cursor results in chunks to handle memory efficiently.

    Args:
        cursor: MongoDB async cursor
        chunk_size: Number of documents to fetch in each chunk

    Yields:
        Chunks of documents

    Example:
        async for chunk in async_stream_cursor(collection.find({}), 1000):
            process_chunk(chunk)
    """
    chunk = []
    async for document in cursor:
        chunk.append(serialize_mongo_doc(document))

        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []

    # Yield remaining documents
    if chunk:
        yield chunk


class AsyncConnectionPool:
    """
    Async connection pool manager for handling multiple MongoDB connections efficiently.

    This is particularly useful for large MongoDB databases where you need to manage
    multiple concurrent connections.
    """

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._pool: List[Any] = []
        self._semaphore = asyncio.Semaphore(max_connections)
        self._lock = asyncio.Lock()

    async def acquire(self) -> Any:
        """Acquire a connection from the pool."""
        await self._semaphore.acquire()
        async with self._lock:
            if self._pool:
                return self._pool.pop()
            return None

    async def release(self, connection: Any) -> None:
        """Release a connection back to the pool."""
        async with self._lock:
            if len(self._pool) < self.max_connections:
                self._pool.append(connection)
        self._semaphore.release()

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            for conn in self._pool:
                if hasattr(conn, 'close'):
                    await conn.close()
            self._pool.clear()


def build_aggregation_pipeline(*stages) -> List[Dict[str, Any]]:
    """
    Build MongoDB aggregation pipeline from stages.

    Args:
        *stages: Aggregation pipeline stages

    Returns:
        List of aggregation stages

    Example:
        pipeline = build_aggregation_pipeline(
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        )
    """
    return list(stages)


def build_text_search_query(search_text: str, language: str = "english") -> Dict[str, Any]:
    """
    Build MongoDB text search query.

    Args:
        search_text: Text to search for
        language: Search language (default: "english")

    Returns:
        MongoDB text search query

    Example:
        query = build_text_search_query("python mongodb")
        # Returns: {"$text": {"$search": "python mongodb", "$language": "english"}}
    """
    return {
        "$text": {
            "$search": search_text,
            "$language": language
        }
    }


def build_geospatial_query(
    field: str,
    geometry_type: str,
    coordinates: List[float],
    max_distance: Optional[float] = None
) -> Dict[str, Any]:
    """
    Build MongoDB geospatial query.

    Args:
        field: Field name containing geospatial data
        geometry_type: GeoJSON geometry type ("Point", "Polygon", etc.)
        coordinates: GeoJSON coordinates
        max_distance: Maximum distance in meters

    Returns:
        MongoDB geospatial query

    Example:
        query = build_geospatial_query(
            "location",
            "Point",
            [-73.9857, 40.7484],  # NYC coordinates
            1000  # 1km radius
        )
    """
    geo_query = {
        field: {
            "$near": {
                "$geometry": {
                    "type": geometry_type,
                    "coordinates": coordinates
                }
            }
        }
    }

    if max_distance:
        geo_query[field]["$near"]["$maxDistance"] = max_distance

    return geo_query
