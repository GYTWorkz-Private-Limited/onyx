"""
Custom exceptions for PostgreSQL DataConnector.

This module defines specific exception types for different error scenarios
to provide clear, actionable error messages for debugging and monitoring.
"""


class DatabaseConnectionError(Exception):
    """
    Raised when PostgreSQL database connection fails.

    This includes scenarios like:
    - Cannot connect to PostgreSQL server
    - Authentication failures (wrong username/password)
    - Network connectivity issues
    - SSL/TLS connection problems
    - Database does not exist
    - Connection timeout
    """
    pass


class QueryExecutionError(Exception):
    """
    Raised when SQL query execution fails.

    This includes scenarios like:
    - SQL syntax errors
    - Table or column not found
    - Data type mismatches
    - Constraint violations (unique, foreign key, check)
    - Transaction rollback failures
    - Permission denied errors
    - PostgreSQL-specific errors (invalid JSON, array operations, etc.)
    """
    pass
