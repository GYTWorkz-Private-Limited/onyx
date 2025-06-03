"""
Async PostgreSQL DataConnector Package

A comprehensive, enterprise-grade asynchronous PostgreSQL database connector built with
asyncpg, designed for high-performance applications with intelligent connection pooling,
ultra-fast COPY operations, and robust error handling optimized for large databases.

Features:
- Asynchronous connection support with asyncpg
- Ultra-fast COPY operations for bulk data transfer
- Advanced JSON/JSONB support for modern applications
- Streaming cursors for large result sets
- Connection pooling with health monitoring
- Automatic retry mechanism for transient failures
- Comprehensive error handling with custom exceptions
- Environment-based configuration management
- Context manager support for automatic resource cleanup
- Transaction management with savepoints
- Full type safety with type hints
- PostgreSQL-specific features support (JSON, Arrays, UUID, etc.)
- SSL/TLS connection support

Author: Augment Agent
Version: 2.0.0
"""

from .async_connector import AsyncPostgreSQLConnector
from .config import Config
from .exceptions import DatabaseConnectionError, QueryExecutionError
from .utils import async_retry, async_batch_processor, async_stream_results

__version__ = "2.0.0"
__author__ = "Augment Agent"
__email__ = "support@augmentcode.com"

__all__ = [
    # Core async connector
    "AsyncPostgreSQLConnector",
    "Config",
    "DatabaseConnectionError",
    "QueryExecutionError",

    # Async utilities
    "async_retry",
    "async_batch_processor",
    "async_stream_results",
]
