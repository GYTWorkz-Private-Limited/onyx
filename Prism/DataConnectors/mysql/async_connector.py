"""
Async MySQL DataConnector - Production-Ready Database Solution

A comprehensive, enterprise-grade async MySQL database connector built with
aiomysql, designed for high-performance operations with intelligent connection
pooling, streaming capabilities, and robust error handling for large databases.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, AsyncIterator, Union
import aiomysql
from aiomysql import Pool, Connection, Cursor

from config import Config
from exceptions import DatabaseConnectionError, QueryExecutionError
from utils import async_retry, async_batch_processor, async_stream_results, AsyncConnectionPool

logger = logging.getLogger(__name__)


class AsyncMySQLConnector:
    """Async MySQL database connector optimized for large databases and high concurrency."""

    def __init__(self, max_connections: int = 20):
        """
        Initialize async MySQL connector with configurable pool settings.

        Args:
            max_connections: Maximum number of connections in the pool
        """
        Config.validate()
        self._pool: Optional[Pool] = None
        self.max_connections = max_connections
        self._connection_pool = AsyncConnectionPool(max_connections)
        logger.info("Async MySQL connector initialized successfully")

    async def _setup_pool(self):
        """Setup aiomysql connection pool with optimized configuration."""
        if self._pool is not None:
            return

        try:
            # Connection parameters
            connection_params = {
                'host': Config.MYSQL_HOST,
                'port': Config.MYSQL_PORT,
                'user': Config.MYSQL_USER,
                'password': Config.MYSQL_PASSWORD,
                'db': Config.MYSQL_DB,
                'minsize': 1,
                'maxsize': self.max_connections,
                'pool_recycle': Config.MYSQL_POOL_RECYCLE,
                'echo': Config.MYSQL_ECHO_SQL,
                'autocommit': False
            }

            # SSL configuration
            if Config.MYSQL_USE_SSL:
                ssl_context = {
                    'ssl': {
                        'ca': Config.MYSQL_SSL_CA
                    } if Config.MYSQL_SSL_CA else True
                }
                connection_params.update(ssl_context)

            self._pool = await aiomysql.create_pool(**connection_params)

            logger.info(f"MySQL connection pool created with {self.max_connections} max connections")

        except Exception as e:
            logger.error(f"Failed to create MySQL connection pool: {e}")
            raise DatabaseConnectionError(f"MySQL connection pool creation failed: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._setup_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()
        return False

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[Connection]:
        """
        Get a connection from the pool with automatic cleanup.

        Yields:
            aiomysql Connection object
        """
        await self._setup_pool()
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            self._pool.release(conn)

    @asynccontextmanager
    async def get_cursor(self, connection: Optional[Connection] = None) -> AsyncIterator[Cursor]:
        """
        Get a cursor with automatic cleanup.

        Args:
            connection: Optional connection to use, if None gets from pool

        Yields:
            aiomysql Cursor object
        """
        if connection:
            cursor = await connection.cursor()
            try:
                yield cursor
            finally:
                await cursor.close()
        else:
            async with self.get_connection() as conn:
                cursor = await conn.cursor()
                try:
                    yield cursor
                finally:
                    await cursor.close()

    # Core async query methods
    @async_retry((aiomysql.Error, Exception), tries=3, delay=2)
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute query and fetch all results asynchronously.

        Args:
            query: SQL query to execute
            params: Query parameters for substitution

        Returns:
            List of dictionaries containing query results
        """
        try:
            async with self.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params or {})
                    result = await cursor.fetchall()
                    return list(result)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}")

    @async_retry((aiomysql.Error, Exception), tries=3, delay=2)
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Execute query and fetch one result asynchronously.

        Args:
            query: SQL query to execute
            params: Query parameters for substitution

        Returns:
            Dictionary containing query result or None
        """
        try:
            async with self.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params or {})
                    result = await cursor.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}")

    @async_retry((aiomysql.Error, Exception), tries=3, delay=2)
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute query and return affected row count asynchronously.

        Args:
            query: SQL query to execute
            params: Query parameters for substitution

        Returns:
            Number of affected rows
        """
        try:
            async with self.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params or {})
                    await conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}")

    @async_retry((aiomysql.Error, Exception), tries=3, delay=2)
    async def execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """
        Execute query with multiple parameter sets asynchronously.

        Args:
            query: SQL query to execute
            params_list: List of parameter dictionaries

        Returns:
            Total number of affected rows
        """
        try:
            async with self.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.executemany(query, params_list)
                    await conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute batch query: {e}")

    # Large database optimized methods
    async def fetch_large_dataset(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Stream large datasets in chunks to handle memory efficiently.

        Args:
            query: SQL query to execute
            params: Query parameters
            chunk_size: Number of rows to fetch in each chunk
            limit: Maximum number of rows to fetch
            offset: Starting offset for pagination

        Yields:
            Chunks of query results
        """
        current_offset = offset
        total_fetched = 0

        while True:
            if limit and total_fetched >= limit:
                break

            # Adjust chunk size if we're near the limit
            current_chunk_size = chunk_size
            if limit and (total_fetched + chunk_size) > limit:
                current_chunk_size = limit - total_fetched

            chunk_query = f"{query} LIMIT {current_chunk_size} OFFSET {current_offset}"
            chunk = await self.fetch_all(chunk_query, params)

            if not chunk:
                break

            yield chunk
            current_offset += len(chunk)
            total_fetched += len(chunk)

            logger.debug(f"Streamed chunk with {len(chunk)} rows (total: {total_fetched})")

    async def bulk_insert(
        self,
        table: str,
        data: List[Dict[str, Any]],
        batch_size: int = 1000,
        on_duplicate_key_update: bool = False
    ) -> bool:
        """
        Perform bulk insert operations optimized for large datasets.

        Args:
            table: Target table name
            data: List of dictionaries containing row data
            batch_size: Number of rows to insert in each batch
            on_duplicate_key_update: Whether to update on duplicate key

        Returns:
            True if successful
        """
        if not data:
            return True

        # Get column names from first row
        columns = list(data[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join(columns)

        base_query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"

        if on_duplicate_key_update:
            update_clause = ', '.join([f"{col} = VALUES({col})" for col in columns])
            base_query += f" ON DUPLICATE KEY UPDATE {update_clause}"

        async def process_batch(batch: List[Dict[str, Any]]) -> int:
            """Process a single batch of inserts."""
            values_list = [[row[col] for col in columns] for row in batch]
            return await self.execute_many(base_query, values_list)

        try:
            results = await async_batch_processor(
                data, batch_size, process_batch
            )

            total_inserted = sum(results)
            logger.info(f"Successfully bulk inserted {total_inserted} rows into {table}")
            return True

        except Exception as e:
            logger.error(f"Bulk insert operation failed: {e}")
            raise QueryExecutionError(f"Failed to bulk insert data into {table}: {e}")

    # Connection health and utility methods
    @async_retry((aiomysql.Error,), tries=3, delay=2)
    async def test_connection(self) -> bool:
        """
        Test database connectivity asynchronously.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            async with self.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    await cursor.fetchone()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def get_table_names(self) -> List[str]:
        """
        Get list of all table names in the database asynchronously.

        Returns:
            List of table names
        """
        try:
            query = "SHOW TABLES"
            result = await self.fetch_all(query)
            # Extract table names from result (format depends on MySQL version)
            table_names = [list(row.values())[0] for row in result]
            return table_names
        except Exception as e:
            logger.error(f"Failed to get table names: {e}")
            raise QueryExecutionError(f"Failed to retrieve table names: {e}")

    async def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database asynchronously.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        try:
            tables = await self.get_table_names()
            return table_name in tables
        except QueryExecutionError:
            return False

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a table including columns and indexes.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary containing table information
        """
        try:
            # Get column information
            columns_query = f"DESCRIBE {table_name}"
            columns = await self.fetch_all(columns_query)

            # Get index information
            indexes_query = f"SHOW INDEX FROM {table_name}"
            indexes = await self.fetch_all(indexes_query)

            # Get table status
            status_query = f"SHOW TABLE STATUS LIKE '{table_name}'"
            status = await self.fetch_one(status_query)

            return {
                'columns': columns,
                'indexes': indexes,
                'status': status
            }
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            raise QueryExecutionError(f"Failed to retrieve table info: {e}")

    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """
        Execute multiple operations in a single transaction.

        Args:
            operations: List of operations, each containing 'query' and optional 'params'

        Returns:
            True if all operations succeeded

        Example:
            operations = [
                {'query': 'INSERT INTO users (name) VALUES (%s)', 'params': ('John',)},
                {'query': 'UPDATE accounts SET balance = balance - %s WHERE user_id = %s', 'params': (100, 1)}
            ]
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await conn.begin()

                    for operation in operations:
                        query = operation['query']
                        params = operation.get('params', ())
                        await cursor.execute(query, params)

                    await conn.commit()
                    logger.info(f"Transaction completed successfully with {len(operations)} operations")
                    return True

                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Transaction failed, rolled back: {e}")
                    raise QueryExecutionError(f"Transaction failed: {e}")

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for monitoring large database performance.

        Returns:
            Dictionary containing database statistics
        """
        try:
            stats = {}

            # Get database size
            size_query = """
                SELECT
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables
                WHERE table_schema = %s
            """
            size_result = await self.fetch_one(size_query, (Config.MYSQL_DB,))
            stats['database_size_mb'] = size_result['size_mb'] if size_result else 0

            # Get table count
            table_count_query = """
                SELECT COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = %s
            """
            table_count = await self.fetch_one(table_count_query, (Config.MYSQL_DB,))
            stats['table_count'] = table_count['table_count'] if table_count else 0

            # Get connection info
            connection_query = "SHOW STATUS LIKE 'Threads_connected'"
            connection_info = await self.fetch_one(connection_query)
            stats['active_connections'] = int(connection_info['Value']) if connection_info else 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise QueryExecutionError(f"Failed to retrieve database statistics: {e}")

    async def close(self):
        """Close all connections and cleanup resources."""
        try:
            if self._pool:
                self._pool.close()
                await self._pool.wait_closed()
                self._pool = None

            await self._connection_pool.close_all()
            logger.info("Async MySQL connector closed successfully")

        except Exception as e:
            logger.error(f"Error closing async connector: {e}")

    # Concurrent operations for high-performance scenarios
    async def execute_concurrent_queries(
        self,
        queries: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Any]:
        """
        Execute multiple queries concurrently for improved performance.

        Args:
            queries: List of query dictionaries with 'query', 'params', and 'type' keys
            max_concurrent: Maximum number of concurrent queries

        Returns:
            List of results in the same order as input queries

        Example:
            queries = [
                {'query': 'SELECT * FROM users WHERE id = %s', 'params': (1,), 'type': 'fetch_one'},
                {'query': 'SELECT COUNT(*) FROM orders', 'params': (), 'type': 'fetch_one'},
                {'query': 'INSERT INTO logs (message) VALUES (%s)', 'params': ('test',), 'type': 'execute'}
            ]
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_query(query_info: Dict[str, Any]) -> Any:
            async with semaphore:
                query = query_info['query']
                params = query_info.get('params', ())
                query_type = query_info.get('type', 'fetch_all')

                if query_type == 'fetch_all':
                    return await self.fetch_all(query, params)
                elif query_type == 'fetch_one':
                    return await self.fetch_one(query, params)
                elif query_type == 'execute':
                    return await self.execute(query, params)
                else:
                    raise ValueError(f"Unknown query type: {query_type}")

        try:
            tasks = [execute_single_query(query_info) for query_info in queries]
            results = await asyncio.gather(*tasks)
            logger.info(f"Executed {len(queries)} concurrent queries successfully")
            return results

        except Exception as e:
            logger.error(f"Concurrent query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute concurrent queries: {e}")

    # Context manager for transactions
    @asynccontextmanager
    async def transaction(self):
        """
        Async context manager for database transactions.

        Example:
            async with connector.transaction() as conn:
                await conn.execute("INSERT INTO users (name) VALUES (%s)", ("John",))
                await conn.execute("UPDATE accounts SET balance = balance - 100 WHERE user_id = 1")
                # Transaction is automatically committed on success or rolled back on error
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await conn.begin()
                    yield cursor
                    await conn.commit()
                except Exception:
                    await conn.rollback()
                    raise
