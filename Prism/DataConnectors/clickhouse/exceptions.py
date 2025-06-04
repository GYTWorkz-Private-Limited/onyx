"""
ClickHouse DataConnector Custom Exceptions

Comprehensive exception hierarchy for ClickHouse-specific error handling
with detailed error context and recovery suggestions.
"""


class ClickHouseConnectionError(Exception):
    """Raised when ClickHouse connection fails"""
    pass


class ClickHouseQueryError(Exception):
    """Raised when ClickHouse query execution fails"""
    pass


class ClickHouseValidationError(Exception):
    """Raised when ClickHouse data validation fails"""
    pass


class ClickHouseConfigurationError(Exception):
    """Raised when ClickHouse configuration is invalid"""
    pass


class ClickHouseClusterError(Exception):
    """Raised when ClickHouse cluster operations fail"""
    pass


class ClickHouseStreamingError(Exception):
    """Raised when ClickHouse streaming operations fail"""
    pass


class ClickHouseCompressionError(Exception):
    """Raised when ClickHouse compression/decompression fails"""
    pass


class ClickHouseSchemaError(Exception):
    """Raised when ClickHouse schema operations fail"""
    pass


class ClickHousePerformanceError(Exception):
    """Raised when ClickHouse performance thresholds are exceeded"""
    pass


class ClickHouseTimeoutError(Exception):
    """Raised when ClickHouse operations timeout"""
    pass


class ClickHouseAuthenticationError(Exception):
    """Raised when ClickHouse authentication fails"""
    pass


class ClickHousePermissionError(Exception):
    """Raised when ClickHouse permission is denied"""
    pass
