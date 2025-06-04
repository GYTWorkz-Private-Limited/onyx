"""
Async PostgreSQL DataConnector - Production-Ready Database Solution

A comprehensive, enterprise-grade async PostgreSQL database connector built with
asyncpg, designed for high-performance operations with intelligent connection
pooling, streaming capabilities, and robust error handling for large databases.

Features:
- Ultra-fast asyncpg driver for maximum performance
- Advanced COPY operations for bulk data transfer
- Streaming cursors for large result sets
- Connection pooling with health monitoring
- JSON/JSONB support for modern applications
- Full transaction management with savepoints
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, AsyncIterator, Union, Tuple
import asyncpg
from asyncpg import Pool, Connection, Record
from asyncpg.exceptions import PostgresError, ConnectionDoesNotExistError
import json
from decimal import Decimal
from datetime import datetime, date, time

from config import Config
from exceptions import DatabaseConnectionError, QueryExecutionError
from utils import async_retry, async_batch_processor, async_stream_results, AsyncConnectionPool

logger = logging.getLogger(__name__)


class AsyncPostgreSQLConnector:
    """Async PostgreSQL database connector optimized for large databases and high performance."""

    def __init__(self, max_connections: int = 20):
        """
        Initialize async PostgreSQL connector with configurable pool settings.

        Args:
            max_connections: Maximum number of connections in the pool
        """
        Config.validate()
        self._pool: Optional[Pool] = None
        self.max_connections = max_connections
        self._connection_pool = AsyncConnectionPool(max_connections)
        logger.info("Async PostgreSQL connector initialized successfully")

    async def _setup_pool(self):
        """Setup asyncpg connection pool with optimized configuration."""
        if self._pool is not None:
            return

        try:
            # Connection parameters
            connection_params = {
                'host': Config.POSTGRES_HOST,
                'port': Config.POSTGRES_PORT,
                'user': Config.POSTGRES_USER,
                'password': Config.POSTGRES_PASSWORD,
                'database': Config.POSTGRES_DB,
                'min_size': 1,
                'max_size': self.max_connections,
                'command_timeout': 60,
                'server_settings': {
                    'application_name': 'AsyncPostgreSQLConnector',
                    'jit': 'off'  # Disable JIT for better performance on small queries
                }
            }

            # SSL configuration
            if Config.POSTGRES_USE_SSL:
                ssl_context = {
                    'ssl': Config.POSTGRES_SSL_MODE or 'require'
                }
                if Config.POSTGRES_SSL_ROOT_CERT:
                    ssl_context['ssl'] = {
                        'ca': Config.POSTGRES_SSL_ROOT_CERT,
                        'check_hostname': False
                    }
                connection_params.update(ssl_context)

            self._pool = await asyncpg.create_pool(**connection_params)

            logger.info(f"PostgreSQL connection pool created with {self.max_connections} max connections")

        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise DatabaseConnectionError(f"PostgreSQL connection pool creation failed: {e}")

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
            asyncpg Connection object
        """
        await self._setup_pool()
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    # Core async query methods
    @async_retry((PostgresError, ConnectionDoesNotExistError), tries=3, delay=2)
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Execute query and fetch all results asynchronously.

        Args:
            query: SQL query to execute
            *args: Query parameters (positional)

        Returns:
            List of dictionaries containing query results
        """
        try:
            async with self.get_connection() as conn:
                records = await conn.fetch(query, *args)
                return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}")

    @async_retry((PostgresError, ConnectionDoesNotExistError), tries=3, delay=2)
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Execute query and fetch one result asynchronously.

        Args:
            query: SQL query to execute
            *args: Query parameters (positional)

        Returns:
            Dictionary containing query result or None
        """
        try:
            async with self.get_connection() as conn:
                record = await conn.fetchrow(query, *args)
                return dict(record) if record else None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}")

    @async_retry((PostgresError, ConnectionDoesNotExistError), tries=3, delay=2)
    async def fetch_val(self, query: str, *args) -> Any:
        """
        Execute query and fetch a single value asynchronously.

        Args:
            query: SQL query to execute
            *args: Query parameters (positional)

        Returns:
            Single value from query result
        """
        try:
            async with self.get_connection() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}")

    @async_retry((PostgresError, ConnectionDoesNotExistError), tries=3, delay=2)
    async def execute(self, query: str, *args) -> str:
        """
        Execute query and return status asynchronously.

        Args:
            query: SQL query to execute
            *args: Query parameters (positional)

        Returns:
            Query execution status
        """
        try:
            async with self.get_connection() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}")

    @async_retry((PostgresError, ConnectionDoesNotExistError), tries=3, delay=2)
    async def execute_many(self, query: str, args_list: List[Tuple]) -> None:
        """
        Execute query with multiple parameter sets asynchronously.

        Args:
            query: SQL query to execute
            args_list: List of parameter tuples
        """
        try:
            async with self.get_connection() as conn:
                await conn.executemany(query, args_list)
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute batch query: {e}")

    # PostgreSQL-specific advanced methods
    async def copy_records_to_table(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> int:
        """
        Use PostgreSQL COPY for ultra-fast bulk inserts.

        Args:
            table_name: Target table name
            records: List of dictionaries containing row data
            columns: Optional list of column names (inferred from first record if None)

        Returns:
            Number of records copied
        """
        if not records:
            return 0

        try:
            # Determine columns
            if columns is None:
                columns = list(records[0].keys())

            # Prepare data for COPY
            copy_data = []
            for record in records:
                row = []
                for col in columns:
                    value = record.get(col)
                    if value is None:
                        row.append(None)
                    elif isinstance(value, (dict, list)):
                        row.append(json.dumps(value))
                    elif isinstance(value, (datetime, date, time)):
                        row.append(value.isoformat())
                    elif isinstance(value, Decimal):
                        row.append(str(value))
                    else:
                        row.append(value)
                copy_data.append(row)

            async with self.get_connection() as conn:
                copied = await conn.copy_records_to_table(
                    table_name,
                    records=copy_data,
                    columns=columns
                )

            logger.info(f"COPY operation completed: {copied} records to {table_name}")
            return len(records)

        except Exception as e:
            logger.error(f"COPY operation failed: {e}")
            raise QueryExecutionError(f"Failed to copy records to {table_name}: {e}")

    async def copy_from_query(
        self,
        query: str,
        output_format: str = 'csv',
        *args
    ) -> AsyncIterator[bytes]:
        """
        Stream query results using PostgreSQL COPY TO.

        Args:
            query: SQL query to execute
            output_format: Output format ('csv', 'binary', 'text')
            *args: Query parameters

        Yields:
            Chunks of data in specified format
        """
        try:
            async with self.get_connection() as conn:
                copy_query = f"COPY ({query}) TO STDOUT WITH {output_format.upper()}"

                async with conn.copy_from_query(copy_query, *args) as copy:
                    async for chunk in copy:
                        yield chunk

        except Exception as e:
            logger.error(f"COPY FROM query failed: {e}")
            raise QueryExecutionError(f"Failed to copy from query: {e}")

    # Large database optimized methods
    async def fetch_large_dataset(
        self,
        query: str,
        *args,
        chunk_size: int = 1000,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Stream large datasets in chunks using cursor-based pagination.

        Args:
            query: SQL query to execute
            *args: Query parameters
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

            # Add LIMIT and OFFSET to query
            paginated_query = f"{query} LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}"
            chunk_args = args + (current_chunk_size, current_offset)

            chunk_records = await self.fetch_all(paginated_query, *chunk_args)

            if not chunk_records:
                break

            yield chunk_records
            current_offset += len(chunk_records)
            total_fetched += len(chunk_records)

            logger.debug(f"Streamed chunk with {len(chunk_records)} rows (total: {total_fetched})")

    async def bulk_insert_with_copy(
        self,
        table: str,
        data: List[Dict[str, Any]],
        batch_size: int = 5000,
        on_conflict: Optional[str] = None
    ) -> bool:
        """
        Perform bulk insert operations using PostgreSQL COPY for maximum performance.

        Args:
            table: Target table name
            data: List of dictionaries containing row data
            batch_size: Number of rows to process in each batch
            on_conflict: Optional conflict resolution (e.g., "DO NOTHING", "DO UPDATE SET ...")

        Returns:
            True if successful
        """
        if not data:
            return True

        async def process_batch(batch: List[Dict[str, Any]]) -> int:
            """Process a single batch using COPY."""
            if on_conflict:
                # For conflict resolution, use regular INSERT with ON CONFLICT
                columns = list(batch[0].keys())
                placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
                column_names = ', '.join(columns)

                insert_query = f"""
                    INSERT INTO {table} ({column_names})
                    VALUES ({placeholders})
                    {on_conflict}
                """

                args_list = [
                    tuple(row[col] for col in columns)
                    for row in batch
                ]

                await self.execute_many(insert_query, args_list)
                return len(batch)
            else:
                # Use COPY for maximum performance
                return await self.copy_records_to_table(table, batch)

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
    @async_retry((PostgresError,), tries=3, delay=2)
    async def test_connection(self) -> bool:
        """
        Test database connectivity asynchronously.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def get_table_names(self, schema: str = 'public') -> List[str]:
        """
        Get list of all table names in the specified schema asynchronously.

        Args:
            schema: Schema name (default: 'public')

        Returns:
            List of table names
        """
        try:
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1 AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            records = await self.fetch_all(query, schema)
            return [record['table_name'] for record in records]
        except Exception as e:
            logger.error(f"Failed to get table names: {e}")
            raise QueryExecutionError(f"Failed to retrieve table names: {e}")

    async def table_exists(self, table_name: str, schema: str = 'public') -> bool:
        """
        Check if a table exists in the database asynchronously.

        Args:
            table_name: Name of the table to check
            schema: Schema name (default: 'public')

        Returns:
            True if table exists, False otherwise
        """
        try:
            query = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = $1 AND table_name = $2
                )
            """
            return await self.fetch_val(query, schema, table_name)
        except Exception:
            return False

    async def get_table_info(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """
        Get detailed information about a table including columns, indexes, and constraints.

        Args:
            table_name: Name of the table
            schema: Schema name (default: 'public')

        Returns:
            Dictionary containing table information
        """
        try:
            # Get column information
            columns_query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
            """
            columns = await self.fetch_all(columns_query, schema, table_name)

            # Get index information
            indexes_query = """
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = $1 AND tablename = $2
            """
            indexes = await self.fetch_all(indexes_query, schema, table_name)

            # Get table size
            size_query = """
                SELECT
                    pg_size_pretty(pg_total_relation_size($1::regclass)) as total_size,
                    pg_size_pretty(pg_relation_size($1::regclass)) as table_size,
                    pg_size_pretty(pg_total_relation_size($1::regclass) - pg_relation_size($1::regclass)) as index_size
            """
            full_table_name = f"{schema}.{table_name}"
            size_info = await self.fetch_one(size_query, full_table_name)

            # Get row count estimate
            count_query = """
                SELECT reltuples::bigint as estimated_rows
                FROM pg_class
                WHERE relname = $1
            """
            count_info = await self.fetch_one(count_query, table_name)

            return {
                'columns': columns,
                'indexes': indexes,
                'size_info': size_info,
                'estimated_rows': count_info['estimated_rows'] if count_info else 0
            }
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            raise QueryExecutionError(f"Failed to retrieve table info: {e}")

    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """
        Execute multiple operations in a single transaction with savepoints.

        Args:
            operations: List of operations, each containing 'query' and optional 'args'

        Returns:
            True if all operations succeeded

        Example:
            operations = [
                {'query': 'INSERT INTO users (name) VALUES ($1)', 'args': ('John',)},
                {'query': 'UPDATE accounts SET balance = balance - $1 WHERE user_id = $2', 'args': (100, 1)}
            ]
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                try:
                    for i, operation in enumerate(operations):
                        query = operation['query']
                        args = operation.get('args', ())

                        # Create savepoint for each operation
                        savepoint_name = f"sp_{i}"
                        await conn.execute(f"SAVEPOINT {savepoint_name}")

                        try:
                            await conn.execute(query, *args)
                        except Exception as e:
                            # Rollback to savepoint on error
                            await conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                            raise e

                    logger.info(f"Transaction completed successfully with {len(operations)} operations")
                    return True

                except Exception as e:
                    logger.error(f"Transaction failed: {e}")
                    raise QueryExecutionError(f"Transaction failed: {e}")

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics for monitoring large database performance.

        Returns:
            Dictionary containing database statistics
        """
        try:
            stats = {}

            # Get database size
            size_query = """
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    pg_database_size(current_database()) as database_size_bytes
            """
            size_result = await self.fetch_one(size_query)
            stats.update(size_result)

            # Get table count
            table_count_query = """
                SELECT COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """
            table_count = await self.fetch_one(table_count_query)
            stats.update(table_count)

            # Get connection info
            connection_query = """
                SELECT
                    count(*) as active_connections,
                    count(*) FILTER (WHERE state = 'active') as active_queries,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
            connection_info = await self.fetch_one(connection_query)
            stats.update(connection_info)

            # Get cache hit ratio
            cache_query = """
                SELECT
                    round(
                        100 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2
                    ) as cache_hit_ratio
                FROM pg_stat_database
                WHERE datname = current_database()
            """
            cache_info = await self.fetch_one(cache_query)
            stats.update(cache_info)

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise QueryExecutionError(f"Failed to retrieve database statistics: {e}")

    async def close(self):
        """Close all connections and cleanup resources."""
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None

            await self._connection_pool.close_all()
            logger.info("Async PostgreSQL connector closed successfully")

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
            queries: List of query dictionaries with 'query', 'args', and 'type' keys
            max_concurrent: Maximum number of concurrent queries

        Returns:
            List of results in the same order as input queries

        Example:
            queries = [
                {'query': 'SELECT * FROM users WHERE id = $1', 'args': (1,), 'type': 'fetch_one'},
                {'query': 'SELECT COUNT(*) FROM orders', 'args': (), 'type': 'fetch_val'},
                {'query': 'INSERT INTO logs (message) VALUES ($1)', 'args': ('test',), 'type': 'execute'}
            ]
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_query(query_info: Dict[str, Any]) -> Any:
            async with semaphore:
                query = query_info['query']
                args = query_info.get('args', ())
                query_type = query_info.get('type', 'fetch_all')

                if query_type == 'fetch_all':
                    return await self.fetch_all(query, *args)
                elif query_type == 'fetch_one':
                    return await self.fetch_one(query, *args)
                elif query_type == 'fetch_val':
                    return await self.fetch_val(query, *args)
                elif query_type == 'execute':
                    return await self.execute(query, *args)
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
                await conn.execute("INSERT INTO users (name) VALUES ($1)", "John")
                await conn.execute("UPDATE accounts SET balance = balance - 100 WHERE user_id = 1")
                # Transaction is automatically committed on success or rolled back on error
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                yield conn

    # JSON/JSONB operations for modern applications
    async def insert_json(self, table: str, json_column: str, data: Dict[str, Any], **kwargs) -> str:
        """
        Insert JSON data into a JSONB column.

        Args:
            table: Target table name
            json_column: Name of the JSONB column
            data: JSON data to insert
            **kwargs: Additional column values

        Returns:
            Execution status
        """
        try:
            columns = [json_column] + list(kwargs.keys())
            placeholders = [f'${i+1}' for i in range(len(columns))]
            values = [json.dumps(data)] + list(kwargs.values())

            query = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """

            return await self.execute(query, *values)

        except Exception as e:
            logger.error(f"JSON insert failed: {e}")
            raise QueryExecutionError(f"Failed to insert JSON data: {e}")

    async def query_json(self, table: str, json_column: str, json_path: str, value: Any) -> List[Dict[str, Any]]:
        """
        Query JSONB data using JSON path expressions.

        Args:
            table: Table name
            json_column: Name of the JSONB column
            json_path: JSON path expression (e.g., '$.user.name')
            value: Value to match

        Returns:
            List of matching records
        """
        try:
            query = f"""
                SELECT * FROM {table}
                WHERE {json_column} #>> $1 = $2
            """

            # Convert JSON path to PostgreSQL array format
            path_parts = json_path.replace('$.', '').split('.')
            return await self.fetch_all(query, path_parts, str(value))

        except Exception as e:
            logger.error(f"JSON query failed: {e}")
            raise QueryExecutionError(f"Failed to query JSON data: {e}")
