"""
Async MySQL DataConnector Package

A comprehensive, enterprise-grade asynchronous MySQL connector built with aiomysql,
designed for high-performance applications with intelligent connection pooling,
streaming capabilities, and robust error handling optimized for large databases.

Features:
- Asynchronous connection support with aiomysql
- Connection pooling with configurable pool sizes
- Streaming large datasets with memory-efficient pagination
- Bulk operations optimized for large data insertions
- Concurrent query execution for parallel operations
- Comprehensive error handling with custom exceptions
- Environment-based configuration management
- Context manager support for automatic resource cleanup
- Transaction management with rollback support
- Full type safety with type hints
- Automatic retry mechanism for transient failures

Author: Augment Agent
Version: 2.0.0
"""

from .async_connector import AsyncMySQLConnector
from .config import Config
from .exceptions import DatabaseConnectionError, QueryExecutionError
from .utils import async_retry, async_batch_processor, async_stream_results

__version__ = "2.0.0"
__author__ = "Augment Agent"
__email__ = "support@augmentcode.com"

__all__ = [
    # Core async connector
    "AsyncMySQLConnector",
    "Config",
    "DatabaseConnectionError",
    "QueryExecutionError",

    # Async utilities
    "async_retry",
    "async_batch_processor",
    "async_stream_results",
]
