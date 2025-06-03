"""
ClickHouse DataConnector Package

A comprehensive, enterprise-grade ClickHouse database connector built for
high-performance analytical workloads with intelligent connection pooling,
robust error handling, and advanced ClickHouse-specific features.

Features:
- HTTP and Native protocol support
- Connection pooling and retry mechanisms
- Batch insert operations with streaming support
- Query optimization and performance monitoring
- Cluster awareness and failover support
- Comprehensive error handling
- Schema introspection and management
- Real-time analytics optimizations

Author: Augment Agent
Version: 1.0.0
"""

from .connector import ClickHouseConnector
from .config import Config
from .exceptions import (
    ClickHouseConnectionError,
    ClickHouseQueryError,
    ClickHouseValidationError,
    ClickHouseConfigurationError,
    ClickHouseClusterError,
    ClickHouseStreamingError,
    ClickHouseCompressionError,
    ClickHouseSchemaError,
    ClickHousePerformanceError,
    ClickHouseTimeoutError,
    ClickHouseAuthenticationError,
    ClickHousePermissionError
)
from .utils import (
    retry,
    format_clickhouse_value,
    build_insert_query,
    optimize_query,
    parse_clickhouse_type,
    validate_table_name,
    estimate_query_cost,
    format_bytes,
    format_duration,
    QueryProfiler
)

__version__ = "1.0.0"
__author__ = "Augment Agent"
__email__ = "support@augmentcode.com"

__all__ = [
    # Core connector
    "ClickHouseConnector",
    "Config",
    
    # Exceptions
    "ClickHouseConnectionError",
    "ClickHouseQueryError",
    "ClickHouseValidationError",
    "ClickHouseConfigurationError",
    "ClickHouseClusterError",
    "ClickHouseStreamingError",
    "ClickHouseCompressionError",
    "ClickHouseSchemaError",
    "ClickHousePerformanceError",
    "ClickHouseTimeoutError",
    "ClickHouseAuthenticationError",
    "ClickHousePermissionError",
    
    # Utilities
    "retry",
    "format_clickhouse_value",
    "build_insert_query",
    "optimize_query",
    "parse_clickhouse_type",
    "validate_table_name",
    "estimate_query_cost",
    "format_bytes",
    "format_duration",
    "QueryProfiler"
]
