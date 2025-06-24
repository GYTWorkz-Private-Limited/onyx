"""
Utility functions for Async MySQL DataConnector.

This module provides helper functions and decorators for enhancing
the reliability and robustness of asynchronous database operations.
"""

import asyncio
from functools import wraps
from typing import Callable, Type, Union, Tuple, AsyncIterator, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def async_retry(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]],
    tries: int = 3,
    delay: float = 1
) -> Callable:
    """
    Async decorator that automatically retries async function calls on specified exceptions.

    This decorator is particularly useful for handling transient database errors
    in async operations like network timeouts, connection drops, or temporary server unavailability.

    Args:
        exceptions: Exception type(s) to catch and retry on
        tries: Maximum number of attempts (default: 3)
        delay: Delay in seconds between retry attempts (default: 1)

    Returns:
        Decorated async function with retry capability

    Example:
        @async_retry((ConnectionError, TimeoutError), tries=3, delay=2)
        async def async_database_operation():
            # This will retry up to 3 times with 2-second delays
            # if ConnectionError or TimeoutError occurs
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < tries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt == tries:
                        # Re-raise the exception if all attempts failed
                        raise
                    # Wait before retrying
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


async def async_batch_processor(
    items: List[Any],
    batch_size: int,
    processor_func: Callable,
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
        async def process_batch(batch, connection):
            return await connection.insert_many(batch)

        results = await async_batch_processor(
            large_dataset, 1000, process_batch, connection
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


async def async_stream_results(
    query_func: Callable,
    chunk_size: int = 1000,
    *args,
    **kwargs
) -> AsyncIterator[List[Any]]:
    """
    Stream large query results in chunks to handle memory efficiently.

    Args:
        query_func: Async function that executes the query
        chunk_size: Number of rows to fetch in each chunk
        *args, **kwargs: Arguments for query_func

    Yields:
        Chunks of query results

    Example:
        async for chunk in async_stream_results(connection.fetch_large_dataset, 1000):
            process_chunk(chunk)
    """
    offset = 0
    while True:
        try:
            chunk = await query_func(*args, limit=chunk_size, offset=offset, **kwargs)
            if not chunk:
                break
            yield chunk
            offset += chunk_size
            logger.debug(f"Streamed chunk with {len(chunk)} rows (offset: {offset})")
        except Exception as e:
            logger.error(f"Failed to stream results at offset {offset}: {e}")
            raise


class AsyncConnectionPool:
    """
    Async connection pool manager for handling multiple database connections efficiently.

    This is particularly useful for large databases where you need to manage
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
