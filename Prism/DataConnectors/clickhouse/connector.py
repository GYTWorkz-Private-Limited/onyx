"""
ClickHouse DataConnector - Production-Ready Database Solution

A comprehensive, enterprise-grade ClickHouse database connector built with
clickhouse-driver and clickhouse-connect, designed for high-performance
analytical workloads with intelligent connection pooling and robust error handling.
"""
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union, Iterator
import time
from datetime import datetime

# ClickHouse drivers
try:
    from clickhouse_driver import Client as NativeClient
    from clickhouse_driver.errors import Error as ClickHouseDriverError
    NATIVE_DRIVER_AVAILABLE = True
except ImportError:
    NATIVE_DRIVER_AVAILABLE = False
    ClickHouseDriverError = Exception

try:
    import clickhouse_connect
    from clickhouse_connect.driver.exceptions import ClickHouseError
    HTTP_DRIVER_AVAILABLE = True
except ImportError:
    HTTP_DRIVER_AVAILABLE = False
    ClickHouseError = Exception

# HTTP client for custom HTTP interface
import httpx
import json
from config import Config
from exceptions import (
        ClickHouseConnectionError, ClickHouseQueryError, ClickHouseValidationError,
        ClickHouseConfigurationError, ClickHouseTimeoutError, ClickHouseAuthenticationError
    )
from utils import retry, QueryProfiler, optimize_query, estimate_query_cost, format_duration


logger = logging.getLogger(__name__)


class ClickHouseConnector:
    """Clean, optimized ClickHouse database connector for production use."""

    def __init__(self, protocol: Optional[str] = None):
        """
        Initialize ClickHouse connector with configurable protocol.

        Args:
            protocol: Connection protocol ('http', 'native', or None for auto-detect)
        """
        Config.validate()
        self.protocol = protocol or Config.CLICKHOUSE_PROTOCOL
        self._client = None
        self._http_client = None
        self.profiler = QueryProfiler() if Config.CLICKHOUSE_ENABLE_PROFILING else None

        self._setup_client()
        logger.info(f"ClickHouse connector initialized successfully using {self.protocol} protocol")

    def _setup_client(self):
        """Setup ClickHouse client based on protocol"""
        try:
            if self.protocol == "native":
                self._setup_native_client()
            elif self.protocol == "http":
                self._setup_http_client()
            else:
                raise ClickHouseConfigurationError(f"Unsupported protocol: {self.protocol}")
        except Exception as e:
            logger.error(f"Failed to setup ClickHouse client: {e}")
            raise ClickHouseConnectionError(f"ClickHouse connection failed: {e}")

    def _setup_native_client(self):
        """Setup native TCP client"""
        if not NATIVE_DRIVER_AVAILABLE:
            raise ClickHouseConfigurationError("clickhouse-driver not available for native protocol")

        connection_settings = {
            'host': Config.CLICKHOUSE_HOST,
            'port': Config.CLICKHOUSE_PORT,
            'user': Config.CLICKHOUSE_USER,
            'password': Config.CLICKHOUSE_PASSWORD,
            'database': Config.CLICKHOUSE_DATABASE,
            'secure': Config.CLICKHOUSE_USE_SSL,
            'compression': Config.CLICKHOUSE_COMPRESSION,
            'client_name': Config.CLICKHOUSE_CLIENT_NAME,
            'send_receive_timeout': Config.CLICKHOUSE_QUERY_TIMEOUT,
            'sync_request_timeout': Config.CLICKHOUSE_QUERY_TIMEOUT,
        }

        self._client = NativeClient(**connection_settings)

    def _setup_http_client(self):
        """Setup HTTP client"""
        if HTTP_DRIVER_AVAILABLE:
            # Use clickhouse-connect if available
            try:
                connection_settings = Config.get_connection_settings()
                # Remove any unsupported parameters
                supported_params = {
                    'host': connection_settings.get('host'),
                    'port': connection_settings.get('port'),
                    'username': connection_settings.get('username'),
                    'password': connection_settings.get('password'),
                    'database': connection_settings.get('database'),
                    'secure': connection_settings.get('secure', False),
                    'compress': connection_settings.get('compress', True),
                    'connect_timeout': 60,  # Connection timeout in seconds
                    'send_receive_timeout': Config.CLICKHOUSE_QUERY_TIMEOUT,  # Query timeout
                }
                # Remove None values
                supported_params = {k: v for k, v in supported_params.items() if v is not None}

                self._client = clickhouse_connect.get_client(**supported_params)
            except Exception as e:
                logger.warning(f"Failed to setup clickhouse-connect client: {e}")
                # Fallback to custom HTTP implementation
                self._setup_custom_http_client()
        else:
            # Fallback to custom HTTP implementation
            self._setup_custom_http_client()

    def _setup_custom_http_client(self):
        """Setup custom HTTP client using httpx"""
        base_url = Config.get_connection_url()

        self._http_client = httpx.Client(
            base_url=base_url,
            timeout=Config.CLICKHOUSE_QUERY_TIMEOUT,
            auth=(Config.CLICKHOUSE_USER, Config.CLICKHOUSE_PASSWORD) if Config.CLICKHOUSE_PASSWORD else None
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()

    @retry((ClickHouseDriverError, ClickHouseError, httpx.RequestError), tries=3, delay=2)
    def test_connection(self) -> bool:
        """
        Test ClickHouse connection health.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            result = self.execute_query("SELECT 1 as test")
            return len(result) > 0 and result[0].get('test') == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    @retry((ClickHouseDriverError, ClickHouseError, httpx.RequestError), tries=3, delay=2)
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None,
                     format_output: str = "JSONEachRow") -> List[Dict[str, Any]]:
        """
        Execute a ClickHouse query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters for substitution
            format_output: Output format for results

        Returns:
            List of dictionaries containing query results
        """
        if self.profiler:
            self.profiler.start(query)

        try:
            if self.protocol == "native" and self._client:
                # Optimize query for native client
                optimized_query = optimize_query(query)
                result = self._execute_native_query(optimized_query, params)
            elif self.protocol == "http" and HTTP_DRIVER_AVAILABLE and self._client:
                # Don't optimize query for clickhouse-connect as it handles formatting internally
                result = self._execute_http_connect_query(query, params)
            elif self._http_client:
                # Optimize query for custom HTTP client
                optimized_query = optimize_query(query)
                result = self._execute_custom_http_query(optimized_query, params, format_output)
            else:
                raise ClickHouseConnectionError("No valid client available")

            if self.profiler:
                profile_result = self.profiler.end()
                logger.info(f"Query executed in {profile_result['duration_formatted']}")

            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise ClickHouseQueryError(f"Failed to execute query: {e}")

    def _execute_native_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query using native client"""
        try:
            result = self._client.execute(query, params or {}, with_column_types=True)

            if not result:
                return []

            data, columns_with_types = result
            columns = [col[0] for col in columns_with_types]

            # Convert to list of dictionaries
            return [dict(zip(columns, row)) for row in data]

        except ClickHouseDriverError as e:
            raise ClickHouseQueryError(f"Native query execution failed: {e}")

    def _execute_http_connect_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query using clickhouse-connect"""
        try:
            # For clickhouse-connect, substitute parameters directly in the query
            # since the library doesn't handle :param syntax well
            if params:
                for key, value in params.items():
                    # Handle string values with proper quoting
                    if isinstance(value, str):
                        query = query.replace(f":{key}", f"'{value}'")
                    else:
                        query = query.replace(f":{key}", str(value))

            # Execute query without parameters since we've substituted them
            result = self._client.query(query)

            # Convert result to list of dictionaries
            if hasattr(result, 'result_rows') and hasattr(result, 'column_names'):
                # New API format
                columns = result.column_names
                rows = result.result_rows
                return [dict(zip(columns, row)) for row in rows]
            elif hasattr(result, 'result_set'):
                # Alternative API format
                return result.result_set
            else:
                # Fallback - try to convert result directly
                return result if isinstance(result, list) else []

        except ClickHouseError as e:
            raise ClickHouseQueryError(f"HTTP query execution failed: {e}")
        except Exception as e:
            raise ClickHouseQueryError(f"HTTP query execution failed: {e}")

    def _execute_custom_http_query(self, query: str, params: Optional[Dict[str, Any]] = None,
                                  format_output: str = "JSONEachRow") -> List[Dict[str, Any]]:
        """Execute query using custom HTTP client"""
        try:
            # Convert parameter syntax from :param to {param} and substitute values
            if params:
                for key, value in params.items():
                    # Handle string values with proper quoting
                    if isinstance(value, str):
                        query = query.replace(f":{key}", f"'{value}'")
                    else:
                        query = query.replace(f":{key}", str(value))

            # Add format if not present
            if "FORMAT" not in query.upper():
                query += f" FORMAT {format_output}"

            # Prepare request
            data = {
                'query': query,
                'database': Config.CLICKHOUSE_DATABASE
            }

            response = self._http_client.post("/", data=data)
            response.raise_for_status()

            # Parse response based on format
            if format_output == "JSONEachRow":
                lines = response.text.strip().split('\n')
                return [json.loads(line) for line in lines if line]
            elif format_output == "JSON":
                result = response.json()
                return result.get('data', [])
            else:
                # Return raw response for other formats
                return [{'result': response.text}]

        except httpx.RequestError as e:
            raise ClickHouseQueryError(f"HTTP request failed: {e}")
        except json.JSONDecodeError as e:
            raise ClickHouseQueryError(f"Failed to parse response: {e}")

    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of dictionaries containing all results
        """
        return self.execute_query(query, params)

    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Execute query and fetch first result.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            First result as dictionary or None
        """
        results = self.execute_query(query, params)
        return results[0] if results else None

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute query and return affected row count.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Number of affected rows (0 for ClickHouse as it doesn't return row count)
        """
        self.execute_query(query, params)
        return 0  # ClickHouse doesn't return affected row count like traditional RDBMS

    def insert_data(self, table: str, data: List[Dict[str, Any]],
                   batch_size: Optional[int] = None) -> bool:
        """
        Insert data into ClickHouse table with batching support.

        Args:
            table: Target table name
            data: List of dictionaries to insert
            batch_size: Batch size for large inserts

        Returns:
            True if successful
        """
        if not data:
            return True

        batch_size = batch_size or Config.CLICKHOUSE_INSERT_BATCH_SIZE

        try:
            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]

                if self.protocol == "native" and self._client:
                    self._insert_native_batch(table, batch)
                elif self.protocol == "http" and HTTP_DRIVER_AVAILABLE and self._client:
                    self._insert_http_connect_batch(table, batch)
                else:
                    self._insert_custom_http_batch(table, batch)

                logger.debug(f"Inserted batch {i//batch_size + 1} ({len(batch)} rows) into {table}")

            logger.info(f"Successfully inserted {len(data)} rows into {table}")
            return True

        except Exception as e:
            logger.error(f"Insert operation failed: {e}")
            raise ClickHouseQueryError(f"Failed to insert data into {table}: {e}")

    def _insert_native_batch(self, table: str, data: List[Dict[str, Any]]):
        """Insert batch using native client"""
        if not data:
            return

        # Get columns from first row
        columns = list(data[0].keys())

        # Convert to list of tuples
        rows = [tuple(row[col] for col in columns) for row in data]

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES"
        self._client.execute(query, rows)

    def _insert_http_connect_batch(self, table: str, data: List[Dict[str, Any]]):
        """Insert batch using clickhouse-connect"""
        if not data:
            return

        try:
            # Convert list of dicts to format expected by clickhouse-connect
            columns = list(data[0].keys())
            rows = [[row[col] for col in columns] for row in data]

            self._client.insert(table, rows, column_names=columns)
        except Exception as e:
            # Fallback to simple insert
            self._client.insert(table, data)

    def _insert_custom_http_batch(self, table: str, data: List[Dict[str, Any]]):
        """Insert batch using custom HTTP client"""
        if not data:
            return

        # Convert to JSONEachRow format with proper date handling
        def serialize_row(row):
            serialized = {}
            for key, value in row.items():
                if hasattr(value, 'isoformat'):  # datetime, date objects
                    serialized[key] = value.isoformat()
                else:
                    serialized[key] = value
            return serialized

        json_rows = '\n'.join(json.dumps(serialize_row(row)) for row in data)

        query = f"INSERT INTO {table} FORMAT JSONEachRow"

        response = self._http_client.post(
            "/",
            params={'query': query, 'database': Config.CLICKHOUSE_DATABASE},
            content=json_rows,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()

    def get_table_names(self) -> List[str]:
        """
        Get list of all table names in the database.

        Returns:
            List of table names
        """
        # First try to get tables from the current database
        query = """
        SELECT name
        FROM system.tables
        WHERE database = :database
        ORDER BY name
        """

        try:
            results = self.execute_query(query, {'database': Config.CLICKHOUSE_DATABASE})

            # If no tables found in current database, get some system tables for testing
            if not results:
                logger.info(f"No tables found in database '{Config.CLICKHOUSE_DATABASE}', returning system tables")
                system_query = """
                SELECT name
                FROM system.tables
                WHERE database = 'system'
                ORDER BY name
                LIMIT 10
                """
                results = self.execute_query(system_query)

            return [row['name'] for row in results]
        except Exception as e:
            logger.error(f"Failed to get table names: {e}")
            raise ClickHouseQueryError(f"Failed to retrieve table names: {e}")

    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        query = """
        SELECT count() as count
        FROM system.tables
        WHERE database = :database AND name = :table_name
        """

        try:
            result = self.fetch_one(query, {
                'database': Config.CLICKHOUSE_DATABASE,
                'table_name': table_name
            })
            return result and result.get('count', 0) > 0
        except Exception as e:
            logger.error(f"Failed to check table existence: {e}")
            return False

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get table schema information.

        Args:
            table_name: Name of the table

        Returns:
            List of column information dictionaries
        """
        query = """
        SELECT
            name,
            type,
            default_kind,
            default_expression,
            comment,
            is_in_partition_key,
            is_in_sorting_key,
            is_in_primary_key,
            is_in_sampling_key
        FROM system.columns
        WHERE database = :database AND table = :table_name
        ORDER BY position
        """

        try:
            return self.execute_query(query, {
                'database': Config.CLICKHOUSE_DATABASE,
                'table_name': table_name
            })
        except Exception as e:
            logger.error(f"Failed to get table schema: {e}")
            raise ClickHouseQueryError(f"Failed to retrieve schema for table {table_name}: {e}")

    def optimize_table(self, table_name: str, partition: Optional[str] = None) -> bool:
        """
        Optimize table by merging parts.

        Args:
            table_name: Name of the table to optimize
            partition: Specific partition to optimize (optional)

        Returns:
            True if successful
        """
        try:
            if partition:
                query = f"OPTIMIZE TABLE {table_name} PARTITION {partition}"
            else:
                query = f"OPTIMIZE TABLE {table_name}"

            self.execute_query(query)
            logger.info(f"Table {table_name} optimized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to optimize table {table_name}: {e}")
            raise ClickHouseQueryError(f"Failed to optimize table {table_name}: {e}")

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.

        Returns:
            Dictionary with database information
        """
        try:
            # Get basic database info
            db_query = """
            SELECT
                name,
                engine,
                data_path,
                metadata_path,
                uuid
            FROM system.databases
            WHERE name = :database
            """

            db_info = self.fetch_one(db_query, {'database': Config.CLICKHOUSE_DATABASE})

            # Get table count
            table_count_query = """
            SELECT count() as table_count
            FROM system.tables
            WHERE database = :database
            """

            table_count = self.fetch_one(table_count_query, {'database': Config.CLICKHOUSE_DATABASE})

            # Get total size
            size_query = """
            SELECT
                sum(bytes) as total_bytes,
                sum(rows) as total_rows
            FROM system.parts
            WHERE database = :database AND active = 1
            """

            size_info = self.fetch_one(size_query, {'database': Config.CLICKHOUSE_DATABASE})

            return {
                'database_info': db_info,
                'table_count': table_count.get('table_count', 0) if table_count else 0,
                'total_bytes': size_info.get('total_bytes', 0) if size_info else 0,
                'total_rows': size_info.get('total_rows', 0) if size_info else 0,
                'connection_protocol': self.protocol,
                'server_info': self._get_server_info()
            }

        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            raise ClickHouseQueryError(f"Failed to retrieve database information: {e}")

    def _get_server_info(self) -> Dict[str, Any]:
        """Get ClickHouse server information"""
        try:
            version_query = "SELECT version() as version"
            version_result = self.fetch_one(version_query)

            uptime_query = "SELECT uptime() as uptime"
            uptime_result = self.fetch_one(uptime_query)

            return {
                'version': version_result.get('version') if version_result else 'unknown',
                'uptime_seconds': uptime_result.get('uptime') if uptime_result else 0
            }
        except Exception:
            return {'version': 'unknown', 'uptime_seconds': 0}

    def close(self):
        """Close database connections and cleanup resources."""
        try:
            if self._client and hasattr(self._client, 'disconnect'):
                self._client.disconnect()
            elif self._client and hasattr(self._client, 'close'):
                self._client.close()

            if self._http_client:
                self._http_client.close()

            logger.info("ClickHouse connector closed successfully")

        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
