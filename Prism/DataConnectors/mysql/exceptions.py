"""
Custom exceptions for MySQL DataConnector.

This module defines specific exception types for different error scenarios
to provide clear, actionable error messages for debugging and monitoring.
"""


class DatabaseConnectionError(Exception):
    """
    Raised when database connection fails.

    This includes scenarios like:
    - Cannot connect to MySQL server
    - Authentication failures
    - Network connectivity issues
    - SSL/TLS connection problems
    """
    pass


class QueryExecutionError(Exception):
    """
    Raised when SQL query execution fails.

    This includes scenarios like:
    - SQL syntax errors
    - Table or column not found
    - Data type mismatches
    - Constraint violations
    - Transaction rollback failures
    """
    pass
