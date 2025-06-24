"""
ClickHouse DataConnector Utilities

Utility functions for ClickHouse operations including retry mechanisms,
data type conversions, query optimization, and performance monitoring.
"""
import time
import logging
from functools import wraps
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date
import json


logger = logging.getLogger(__name__)


def retry(exceptions, tries=3, delay=1, backoff=2, max_delay=60):
    """
    Retry decorator with exponential backoff for ClickHouse operations
    
    Args:
        exceptions: Exception types to catch and retry
        tries: Maximum number of attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        max_delay: Maximum delay between retries
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < tries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt == tries:
                        logger.error(f"Function {func.__name__} failed after {tries} attempts: {e}")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay = min(current_delay * backoff, max_delay)
            
        return wrapper
    return decorator


def format_clickhouse_value(value: Any) -> str:
    """
    Format Python values for ClickHouse queries
    
    Args:
        value: Python value to format
        
    Returns:
        Formatted string for ClickHouse
    """
    if value is None:
        return "NULL"
    elif isinstance(value, bool):
        return "1" if value else "0"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Escape single quotes and wrap in quotes
        escaped = value.replace("'", "\\'")
        return f"'{escaped}'"
    elif isinstance(value, (datetime, date)):
        return f"'{value.isoformat()}'"
    elif isinstance(value, (list, tuple)):
        formatted_items = [format_clickhouse_value(item) for item in value]
        return f"[{', '.join(formatted_items)}]"
    elif isinstance(value, dict):
        return f"'{json.dumps(value)}'"
    else:
        return f"'{str(value)}'"


def build_insert_query(table: str, data: List[Dict[str, Any]], 
                      on_duplicate: Optional[str] = None) -> str:
    """
    Build optimized INSERT query for ClickHouse
    
    Args:
        table: Target table name
        data: List of dictionaries with data to insert
        on_duplicate: Action on duplicate keys (not applicable for ClickHouse)
        
    Returns:
        Formatted INSERT query
    """
    if not data:
        raise ValueError("No data provided for insert")
    
    # Get columns from first row
    columns = list(data[0].keys())
    columns_str = ", ".join(columns)
    
    # Build VALUES clause
    values_list = []
    for row in data:
        row_values = [format_clickhouse_value(row.get(col)) for col in columns]
        values_list.append(f"({', '.join(row_values)})")
    
    values_str = ", ".join(values_list)
    
    return f"INSERT INTO {table} ({columns_str}) VALUES {values_str}"


def optimize_query(query: str) -> str:
    """
    Apply ClickHouse-specific query optimizations
    
    Args:
        query: Original SQL query
        
    Returns:
        Optimized query
    """
    # Remove unnecessary whitespace
    query = " ".join(query.split())
    
    # Add FINAL if needed for ReplacingMergeTree tables
    if "SELECT" in query.upper() and "FINAL" not in query.upper():
        # This is a basic heuristic - in production, you'd want more sophisticated logic
        pass
    
    # Add FORMAT clause if not present for better performance
    if "FORMAT" not in query.upper() and query.upper().startswith("SELECT"):
        query += " FORMAT JSONEachRow"
    
    return query


def parse_clickhouse_type(clickhouse_type: str) -> str:
    """
    Convert ClickHouse data type to Python equivalent
    
    Args:
        clickhouse_type: ClickHouse column type
        
    Returns:
        Python type name
    """
    type_mapping = {
        'UInt8': 'int',
        'UInt16': 'int',
        'UInt32': 'int',
        'UInt64': 'int',
        'Int8': 'int',
        'Int16': 'int',
        'Int32': 'int',
        'Int64': 'int',
        'Float32': 'float',
        'Float64': 'float',
        'String': 'str',
        'FixedString': 'str',
        'Date': 'date',
        'DateTime': 'datetime',
        'DateTime64': 'datetime',
        'UUID': 'str',
        'IPv4': 'str',
        'IPv6': 'str',
        'Enum8': 'str',
        'Enum16': 'str',
        'Array': 'list',
        'Tuple': 'tuple',
        'Nullable': 'Optional',
    }
    
    # Handle complex types
    if clickhouse_type.startswith('Nullable('):
        inner_type = clickhouse_type[9:-1]
        return f"Optional[{parse_clickhouse_type(inner_type)}]"
    elif clickhouse_type.startswith('Array('):
        inner_type = clickhouse_type[6:-1]
        return f"List[{parse_clickhouse_type(inner_type)}]"
    elif clickhouse_type.startswith('Tuple('):
        return 'tuple'
    elif clickhouse_type.startswith('FixedString('):
        return 'str'
    elif clickhouse_type.startswith('Decimal'):
        return 'float'
    
    # Return mapped type or default to string
    return type_mapping.get(clickhouse_type, 'str')


def validate_table_name(table_name: str) -> bool:
    """
    Validate ClickHouse table name
    
    Args:
        table_name: Table name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not table_name:
        return False
    
    # ClickHouse table names can contain letters, numbers, and underscores
    # Must start with letter or underscore
    import re
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, table_name))


def estimate_query_cost(query: str, row_count: int = 0) -> Dict[str, Any]:
    """
    Estimate query execution cost and provide optimization suggestions
    
    Args:
        query: SQL query to analyze
        row_count: Estimated number of rows to process
        
    Returns:
        Dictionary with cost estimation and suggestions
    """
    cost_info = {
        'estimated_cost': 'low',
        'suggestions': [],
        'warnings': []
    }
    
    query_upper = query.upper()
    
    # Check for expensive operations
    if 'ORDER BY' in query_upper and 'LIMIT' not in query_upper:
        cost_info['estimated_cost'] = 'high'
        cost_info['suggestions'].append("Consider adding LIMIT clause to ORDER BY queries")
    
    if 'GROUP BY' in query_upper and row_count > 1000000:
        cost_info['estimated_cost'] = 'medium'
        cost_info['suggestions'].append("Consider using sampling for large GROUP BY operations")
    
    if 'JOIN' in query_upper:
        cost_info['estimated_cost'] = 'medium'
        cost_info['suggestions'].append("Ensure JOIN conditions use indexed columns")
    
    if '*' in query and 'SELECT *' in query_upper:
        cost_info['warnings'].append("SELECT * can be inefficient - specify needed columns")
    
    if 'DISTINCT' in query_upper and row_count > 100000:
        cost_info['estimated_cost'] = 'high'
        cost_info['suggestions'].append("DISTINCT on large datasets can be expensive")
    
    return cost_info


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes into human-readable string
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration into human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1m 30s")
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


class QueryProfiler:
    """Simple query profiler for performance monitoring"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.query = None
    
    def start(self, query: str):
        """Start profiling a query"""
        self.query = query
        self.start_time = time.time()
        logger.debug(f"Starting query execution: {query[:100]}...")
    
    def end(self):
        """End profiling and return results"""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        result = {
            'query': self.query,
            'duration_seconds': duration,
            'duration_formatted': format_duration(duration),
            'start_time': self.start_time,
            'end_time': self.end_time
        }
        
        logger.debug(f"Query completed in {format_duration(duration)}")
        return result
