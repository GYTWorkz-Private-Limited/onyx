# ⚡ ClickHouse DataConnector

## 🏆 Why This Connector Is Reliable

This ClickHouse connector provides a **solid, well-tested solution** for analytical applications. Built with both `clickhouse-driver` and `clickhouse-connect`, it delivers good performance for OLAP workloads with connection management and robust error handling.

### ✅ Key Features Implemented

#### **1. Dual Protocol Support**
- **HTTP protocol** - Firewall-friendly (port 8123)
- **Native TCP protocol** - Direct connections (port 9000)
- **Connection management** with proper cleanup
- **Context manager support** for automatic resource management

#### **2. Robust Error Handling**
- **Custom exception hierarchy** with specific error types (ClickHouseConnectionError, ClickHouseQueryError, etc.)
- **Automatic retry mechanisms** with exponential backoff for transient failures
- **Comprehensive logging** for debugging and monitoring

#### **3. Core Optimizations**
- **Compression support** (LZ4, ZSTD, GZIP) for optimal data transfer
- **Batch operations** for efficient data insertion
- **Query profiling** for performance monitoring

#### **4. Security & Configuration**
- **SSL/TLS support** for both HTTP and Native protocols
- **Environment-based configuration** for different deployment stages
- **Connection parameter validation** and sanitization


---

## 🚀 Key Features

### Core Database Operations
- **Dual protocol support** - HTTP and Native TCP
- **Connection management** with proper resource cleanup
- **Compression support** (LZ4, ZSTD, GZIP) for efficient data transfer
- **Batch processing** with configurable chunk sizes

### ClickHouse Integration
- **Query execution** with parameter support
- **Schema introspection** and table management
- **Data type handling** for ClickHouse-specific types
- **System table access** for monitoring and administration

### Reliability Features
- **Connection health monitoring** with test methods
- **SSL/TLS encryption** for secure connections
- **Comprehensive error handling** with specific exception types
- **Performance monitoring** with query profiling
- **Retry mechanisms** with exponential backoff

### Why ClickHouse?
- **Fast Analytics**: Optimized for analytical queries
- **Compression**: Superior compression ratios for storage efficiency
- **Scalable**: Built for large-scale data processing
- **Flexible**: Multiple data types and query capabilities

## Implementation Details

### Core Capabilities
- **Multiple Protocols**: HTTP and Native TCP protocol support
- **Connection Management**: Proper connection lifecycle with cleanup
- **Batch Operations**: Bulk insert operations with configurable batch sizes
- **Error Handling**: Comprehensive exception handling with retry mechanisms
- **Configuration Management**: Environment-based configuration with validation
- **Performance Monitoring**: Built-in query profiling and performance tracking

### Protocol Support
- **HTTP Protocol**: Firewall-friendly, load balancer compatible (Port 8123)
- **Native Protocol**: Direct connections for better performance (Port 9000)
- **SSL/TLS**: Secure connections for both protocols
- **Compression**: LZ4, ZSTD, GZIP compression support

### Database Operations
- **Schema Management**: Table introspection and management
- **Data Types**: ClickHouse data type support with Python mapping
- **Query Execution**: Parameterized queries with result formatting

## Installation

### Prerequisites
- Python 3.8+
- ClickHouse server (local or remote)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Required Packages
```bash
pip install clickhouse-driver clickhouse-connect httpx python-dotenv
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
# Required Settings
CLICKHOUSE_HOST=localhost
CLICKHOUSE_DATABASE=default
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# Protocol Configuration
CLICKHOUSE_PROTOCOL=http  # 'http' or 'native'
CLICKHOUSE_PORT=8123      # Auto-configured based on protocol
CLICKHOUSE_USE_SSL=false

# Connection Pool Settings (configurable via .env)
CLICKHOUSE_POOL_SIZE=10
CLICKHOUSE_MAX_OVERFLOW=20
CLICKHOUSE_POOL_TIMEOUT=30
CLICKHOUSE_POOL_RECYCLE=3600
CLICKHOUSE_POOL_PRE_PING=true

# Performance Settings
CLICKHOUSE_COMPRESSION=lz4
CLICKHOUSE_INSERT_BATCH_SIZE=10000
CLICKHOUSE_QUERY_TIMEOUT=300
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `CLICKHOUSE_HOST` | Required | ClickHouse server hostname |
| `CLICKHOUSE_DATABASE` | Required | Target database name |
| `CLICKHOUSE_USER` | `default` | Database username |
| `CLICKHOUSE_PASSWORD` | `""` | Database password |
| `CLICKHOUSE_PROTOCOL` | `http` | Connection protocol (`http` or `native`) |
| `CLICKHOUSE_POOL_SIZE` | `10` | Base connection pool size |
| `CLICKHOUSE_COMPRESSION` | `lz4` | Data compression method |

## Usage

### Basic Connection

```python
from connector import ClickHouseConnector

# Always use context manager for automatic cleanup
with ClickHouseConnector() as db:
    # Test connection health
    if db.test_connection():
        print("✓ ClickHouse connected and healthy")

    # Execute queries
    results = db.fetch_all("SELECT version()")
    print(f"ClickHouse version: {results[0]['version()']}")
```

### Query Operations

```python
with ClickHouseConnector() as db:
    # Single row query
    user = db.fetch_one("SELECT * FROM users WHERE id = 123")

    # Multiple rows query
    events = db.fetch_all("""
        SELECT event_name, count() as total
        FROM events
        WHERE date >= today() - 7
        GROUP BY event_name
        ORDER BY total DESC
        LIMIT 10
    """)

    # Execute DDL/DML without results
    db.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            date Date,
            user_id UInt32,
            event String,
            value Float64
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (date, user_id)
    """)
```

### Batch Data Operations

```python
# High-performance bulk insert
data = [
    {'date': '2024-01-01', 'user_id': 1, 'event': 'click', 'value': 100.5},
    {'date': '2024-01-01', 'user_id': 2, 'event': 'view', 'value': 200.3},
    # ... more data
]

with ClickHouseConnector() as db:
    # Automatic batching for large datasets
    db.insert_data('analytics', data, batch_size=10000)
```

### Schema Management

```python
with ClickHouseConnector() as db:
    # List all tables
    tables = db.get_table_names()
    print(f"Found {len(tables)} tables")

    # Check if table exists
    if db.table_exists('events'):
        # Get table schema
        schema = db.get_table_schema('events')
        for column in schema:
            print(f"{column['name']}: {column['type']}")

    # Get database information
    info = db.get_database_info()
    print(f"Database: {info['database_info']['name']}")
    print(f"Total tables: {info['table_count']}")
```

## API Reference

### Core Methods

#### `test_connection() -> bool`
Test ClickHouse connection health.
- **Returns**: `True` if connection is healthy, `False` otherwise
- **Use Case**: Health checks and connection validation

#### `execute_query(query: str, params: Dict = None) -> List[Dict]`
Execute a ClickHouse query and return results.
- **Parameters**:
  - `query`: SQL query to execute
  - `params`: Optional query parameters for substitution
- **Returns**: List of dictionaries containing query results
- **Use Case**: General query execution

#### `fetch_all(query: str, params: Dict = None) -> List[Dict]`
Execute query and fetch all results.
- **Parameters**: Same as `execute_query`
- **Returns**: List of dictionaries containing all results
- **Use Case**: Data retrieval operations

#### `fetch_one(query: str, params: Dict = None) -> Dict | None`
Execute query and fetch first result.
- **Parameters**: Same as `execute_query`
- **Returns**: First result as dictionary or `None`
- **Use Case**: Single row queries

#### `execute(query: str, params: Dict = None) -> int`
Execute query without returning results.
- **Parameters**: Same as `execute_query`
- **Returns**: Number of affected rows (always 0 for ClickHouse)
- **Use Case**: DDL operations, INSERT/UPDATE statements

### Data Operations

#### `insert_data(table: str, data: List[Dict], batch_size: int = None) -> bool`
Insert data into ClickHouse table with batching support.
- **Parameters**:
  - `table`: Target table name
  - `data`: List of dictionaries to insert
  - `batch_size`: Optional batch size for large inserts
- **Returns**: `True` if successful
- **Use Case**: Bulk data insertion with automatic batching

### Schema Operations

#### `get_table_names() -> List[str]`
Get list of all table names in the database.
- **Returns**: List of table names
- **Use Case**: Schema discovery

#### `table_exists(table_name: str) -> bool`
Check if table exists in the database.
- **Parameters**: `table_name`: Name of the table to check
- **Returns**: `True` if table exists, `False` otherwise
- **Use Case**: Conditional table operations

#### `get_table_schema(table_name: str) -> List[Dict]`
Get table schema information.
- **Parameters**: `table_name`: Name of the table
- **Returns**: List of dictionaries with column information
- **Use Case**: Schema inspection and validation

### Utility Methods

#### `get_database_info() -> Dict`
Get comprehensive database information and statistics.
- **Returns**: Dictionary with database metadata
- **Use Case**: Monitoring and administration

#### `optimize_table(table_name: str, partition: str = None) -> bool`
Optimize table by merging parts.
- **Parameters**:
  - `table_name`: Name of the table to optimize
  - `partition`: Specific partition to optimize (optional)
- **Returns**: `True` if successful
- **Use Case**: Table maintenance and optimization

#### `close() -> None`
Cleanup connections and resources.
- **Returns**: None
- **Use Case**: Manual resource cleanup (automatic with context manager)

## Best Practices

### Connection Management
- **Always use context managers** for automatic resource cleanup
- **Reuse connections** within the same context for multiple operations
- **Test connections** before performing operations

```python
# ✅ Good: Use context manager
with ClickHouseConnector() as db:
    if db.test_connection():
        result1 = db.fetch_all("SELECT * FROM table1")
        result2 = db.fetch_all("SELECT * FROM table2")

# ❌ Bad: Creating new connections repeatedly
for query in queries:
    with ClickHouseConnector() as db:
        db.execute_query(query)
```

### Query Optimization
- **Use LIMIT clauses** for large result sets
- **Specify columns explicitly** instead of SELECT *
- **Use appropriate WHERE clauses** to filter data early
- **Test queries** before running on large datasets

```python
# ✅ Good: Optimized query
db.fetch_all("""
    SELECT user_id, count() as events
    FROM user_events
    WHERE date >= today() - 7
    GROUP BY user_id
    ORDER BY events DESC
    LIMIT 1000
""")

# ❌ Bad: Unoptimized query
db.fetch_all("SELECT * FROM user_events")
```

### Data Operations
- **Use batch operations** for bulk inserts
- **Configure appropriate batch sizes** based on your data and memory constraints
- **Handle errors gracefully** with proper exception handling

```python
# ✅ Good: Batch insert
db.insert_data('events', large_dataset, batch_size=10000)

# ❌ Bad: Row-by-row insert
for row in large_dataset:
    db.insert_data('events', [row])
```

### Error Handling
- **Use specific exception types** for different error scenarios
- **Implement retry logic** for transient failures
- **Log errors appropriately** for debugging and monitoring

```python
from exceptions import ClickHouseConnectionError, ClickHouseQueryError

try:
    with ClickHouseConnector() as db:
        result = db.execute_query("SELECT * FROM events")
except ClickHouseConnectionError:
    logger.error("ClickHouse server unavailable")
except ClickHouseQueryError as e:
    logger.error(f"Query failed: {e}")
```

#### Memory Issues

**Issue**: `Memory limit exceeded` errors

**Solutions**:
1. Reduce batch sizes for large operations
2. Use streaming for large result sets
3. Optimize queries to process less data
4. Configure appropriate memory limits in ClickHouse

#### Authentication Errors

**Issue**: `ClickHouseAuthenticationError`

**Solutions**:
1. Verify username and password in `.env` file
2. Check user permissions in ClickHouse
3. Ensure user has access to the specified database

### Performance Tips

1. **Use appropriate data types** in ClickHouse schemas
2. **Partition tables** by date or other logical divisions
3. **Use compression** for better storage efficiency
4. **Monitor query performance** with profiling enabled
5. **Batch operations** for better throughput

### Logging and Debugging

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed connection and query information
with ClickHouseConnector() as db:
    result = db.fetch_all("SELECT 1")
```

## Project Structure

```
clickhouse/
├── README.md              # This documentation
├── requirements.txt       # Python dependencies
├── __init__.py           # Package initialization
├── connector.py          # Main ClickHouseConnector class
├── config.py             # Configuration management
├── exceptions.py         # Custom exception classes
├── utils.py              # Utility functions and helpers
└── test_db.py           # Test suite
```

### Core Components

- **`connector.py`**: Main ClickHouseConnector class with all database operations
- **`config.py`**: Environment-based configuration with validation
- **`exceptions.py`**: Custom exception hierarchy for error handling
- **`utils.py`**: Utility functions for retry logic, query optimization, and data formatting
- **`test_db.py`**: Comprehensive test suite for validation

---

## 📈 Performance Characteristics

### Expected Performance
- **Query execution**: Depends on query complexity and data size
- **Bulk inserts**: Efficient with batch processing
- **Connection overhead**: Minimal with proper connection reuse
- **Memory usage**: Scales with result set size

### ClickHouse Advantages
- **Columnar storage** for analytical query optimization
- **Compression algorithms** (LZ4, ZSTD) for optimal data transfer
- **MergeTree engine** optimizations for time-series data
- **Built-in functions** for analytical operations

### Performance Tips
- **Use appropriate batch sizes** for bulk operations
- **Leverage ClickHouse-specific functions** for better performance
- **Monitor query execution time** with built-in profiling
- **Test with representative data sizes** before production use

## 🚀 Deployment

### Environment Configuration

```bash
# Environment Variables
export CLICKHOUSE_HOST=your-clickhouse-server.com
export CLICKHOUSE_USER=your_user
export CLICKHOUSE_PASSWORD="your_password"
export CLICKHOUSE_DATABASE=your_database
export CLICKHOUSE_PROTOCOL=http  # or 'native'
export CLICKHOUSE_PORT=8123  # 9000 for native
export CLICKHOUSE_USE_SSL=true
export CLICKHOUSE_COMPRESSION=lz4
export CLICKHOUSE_QUERY_TIMEOUT=300
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - CLICKHOUSE_HOST=clickhouse
      - CLICKHOUSE_USER=analytics_user
      - CLICKHOUSE_PASSWORD=secure_password
      - CLICKHOUSE_DATABASE=analytics_db
      - CLICKHOUSE_PROTOCOL=http
      - CLICKHOUSE_POOL_SIZE=15
    depends_on:
      clickhouse:
        condition: service_healthy

  clickhouse:
    image: clickhouse/clickhouse-server:latest
    environment:
      - CLICKHOUSE_DB=analytics_db
      - CLICKHOUSE_USER=analytics_user
      - CLICKHOUSE_PASSWORD=secure_password
    ports:
      - "8123:8123"  # HTTP
      - "9000:9000"  # Native
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8123/ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  clickhouse_data:
```

### Health Checks & Monitoring

```python
from connector import ClickHouseConnector

def health_check():
    """Simple health check function"""
    try:
        with ClickHouseConnector() as db:
            is_connected = db.test_connection()
            if is_connected:
                info = db.get_database_info()
                return {
                    "status": "healthy",
                    "database": "connected",
                    "tables": info.get("table_count", 0)
                }
            else:
                return {"status": "unhealthy", "error": "Connection failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def readiness_check():
    """Check if database is ready for queries"""
    try:
        with ClickHouseConnector() as db:
            result = db.fetch_one("SELECT 1 as ready")
            if result and result.get('ready') == 1:
                return {"status": "ready"}
            else:
                return {"status": "not_ready"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

## 🔒 Security Best Practices

### SSL/TLS Configuration
```python
# SSL Configuration for production
import os

# Environment variables for SSL
os.environ['CLICKHOUSE_USE_SSL'] = 'true'
os.environ['CLICKHOUSE_SSL_CERT'] = '/path/to/client-cert.pem'
os.environ['CLICKHOUSE_SSL_KEY'] = '/path/to/client-key.pem'
os.environ['CLICKHOUSE_SSL_CA'] = '/path/to/ca-cert.pem'

# Connection with SSL
connector = ClickHouseConnector()
```

### User Management & Permissions
```sql
-- Create analytical users with appropriate permissions
CREATE USER analytics_reader IDENTIFIED BY 'secure_password';
CREATE USER analytics_writer IDENTIFIED BY 'secure_password';
CREATE USER analytics_admin IDENTIFIED BY 'secure_password';

-- Grant appropriate permissions
GRANT SELECT ON analytics_db.* TO analytics_reader;
GRANT SELECT, INSERT ON analytics_db.* TO analytics_writer;
GRANT ALL ON analytics_db.* TO analytics_admin;

-- Create profiles for resource management
CREATE SETTINGS PROFILE analytics_profile SETTINGS max_memory_usage = 10000000000;
ALTER USER analytics_reader SETTINGS PROFILE 'analytics_profile';
```

### Query Security & Validation
```python
# Input validation for queries
def validate_query(query: str, allowed_tables: list):
    """Basic query validation"""
    # Prevent dangerous operations
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
    query_upper = query.upper()

    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise ValueError(f"Dangerous operation '{keyword}' not allowed")

    return True

# Safe query execution
def safe_query_execution(query: str, params: dict = None):
    """Execute query with basic validation"""
    validate_query(query, ['events', 'users', 'analytics'])

    with ClickHouseConnector() as db:
        return db.execute_query(query, params)
```

## 🎯 Use Cases & Recommendations

### When to Use ClickHouse Connector

#### ✅ **Good For:**
- **Analytics** and business intelligence
- **Time-series data** and event tracking
- **Log analysis** and monitoring systems
- **Data warehousing** with columnar storage benefits
- **OLAP workloads** with analytical queries
- **Reporting** and dashboard data sources

#### ⚠️ **Consider Alternatives For:**
- **OLTP workloads** with frequent updates (consider PostgreSQL or MySQL)
- **Document storage** with flexible schemas (consider MongoDB)
- **Simple key-value operations** (consider Redis)
- **Complex transactions** requiring ACID compliance across multiple tables
- **Real-time streaming** requirements (consider specialized streaming solutions)
