"""
ClickHouse DataConnector Configuration

Comprehensive configuration management for ClickHouse connections
with support for HTTP/Native protocols, clustering, and performance tuning.
"""
import os
from typing import Dict, List, Optional


class Config:
    """Configuration for ClickHouse database connection"""

    # Basic Connection Settings
    CLICKHOUSE_HOST = None
    CLICKHOUSE_PORT = 8123
    CLICKHOUSE_USER = None
    CLICKHOUSE_PASSWORD = None
    CLICKHOUSE_DATABASE = None
    CLICKHOUSE_PROTOCOL = "http"  # http or native

    # HTTP-specific settings
    CLICKHOUSE_HTTP_PORT = 8123
    CLICKHOUSE_HTTPS_PORT = 8443
    CLICKHOUSE_USE_SSL = False

    # Native protocol settings
    CLICKHOUSE_NATIVE_PORT = 9000
    CLICKHOUSE_SECURE_NATIVE_PORT = 9440

    # Authentication
    CLICKHOUSE_AUTH_METHOD = "password"  # password, key, none
    CLICKHOUSE_CLIENT_NAME = "python-clickhouse-connector"

    # Connection Pool Settings
    CLICKHOUSE_POOL_SIZE = 10
    CLICKHOUSE_MAX_OVERFLOW = 20
    CLICKHOUSE_POOL_TIMEOUT = 30
    CLICKHOUSE_POOL_RECYCLE = 3600
    CLICKHOUSE_POOL_PRE_PING = True

    # Query Settings
    CLICKHOUSE_QUERY_TIMEOUT = 300
    CLICKHOUSE_INSERT_TIMEOUT = 60
    CLICKHOUSE_SELECT_TIMEOUT = 300
    CLICKHOUSE_MAX_QUERY_SIZE = 262144  # 256KB
    CLICKHOUSE_MAX_RESULT_ROWS = 1000000

    # Performance Settings
    CLICKHOUSE_COMPRESSION = "lz4"  # lz4, zstd, gzip, none
    CLICKHOUSE_COMPRESSION_LEVEL = 1
    CLICKHOUSE_INSERT_BATCH_SIZE = 10000
    CLICKHOUSE_ENABLE_STREAMING = True
    CLICKHOUSE_BUFFER_SIZE = 8192

    # Caching
    CLICKHOUSE_CACHE_RESULTS = False
    CLICKHOUSE_CACHE_TTL = 300
    CLICKHOUSE_CACHE_MAX_SIZE = 100

    # Cluster Settings
    CLICKHOUSE_CLUSTER_NODES = None  # comma-separated list
    CLICKHOUSE_CLUSTER_NAME = None
    CLICKHOUSE_AUTO_FAILOVER = True
    CLICKHOUSE_LOAD_BALANCING = "round_robin"  # round_robin, random, first_live

    # Monitoring and Logging
    CLICKHOUSE_ENABLE_PROFILING = False
    CLICKHOUSE_LOG_QUERIES = False
    CLICKHOUSE_LOG_LEVEL = "INFO"
    CLICKHOUSE_METRICS_ENABLED = False

    # Advanced Settings
    CLICKHOUSE_READONLY = False
    CLICKHOUSE_EXTREMES = False
    CLICKHOUSE_QUOTA_KEY = None
    CLICKHOUSE_SETTINGS = None  # JSON string of additional settings

    @classmethod
    def validate(cls):
        """Load and validate environment variables"""
        # Required variables
        required_vars = {
            'CLICKHOUSE_HOST': os.getenv("CLICKHOUSE_HOST"),
            'CLICKHOUSE_DATABASE': os.getenv("CLICKHOUSE_DATABASE")
        }

        # Set values and check for missing variables
        missing = []
        for key, value in required_vars.items():
            setattr(cls, key, value)
            if value is None:
                missing.append(key)

        if missing:
            raise ValueError(f"Missing required config variables: {', '.join(missing)}")

        # Optional variables with defaults
        cls.CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
        cls.CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
        cls.CLICKHOUSE_PROTOCOL = os.getenv("CLICKHOUSE_PROTOCOL", "http").lower()

        # Port configuration based on protocol and SSL
        cls.CLICKHOUSE_USE_SSL = os.getenv("CLICKHOUSE_USE_SSL", "false").lower() == "true"

        if cls.CLICKHOUSE_PROTOCOL == "http":
            default_port = cls.CLICKHOUSE_HTTPS_PORT if cls.CLICKHOUSE_USE_SSL else cls.CLICKHOUSE_HTTP_PORT
        else:  # native
            default_port = cls.CLICKHOUSE_SECURE_NATIVE_PORT if cls.CLICKHOUSE_USE_SSL else cls.CLICKHOUSE_NATIVE_PORT

        cls.CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", default_port))

        # Connection Pool settings
        cls.CLICKHOUSE_POOL_SIZE = int(os.getenv("CLICKHOUSE_POOL_SIZE", 10))
        cls.CLICKHOUSE_MAX_OVERFLOW = int(os.getenv("CLICKHOUSE_MAX_OVERFLOW", 20))
        cls.CLICKHOUSE_POOL_TIMEOUT = int(os.getenv("CLICKHOUSE_POOL_TIMEOUT", 30))
        cls.CLICKHOUSE_POOL_RECYCLE = int(os.getenv("CLICKHOUSE_POOL_RECYCLE", 3600))
        cls.CLICKHOUSE_POOL_PRE_PING = os.getenv("CLICKHOUSE_POOL_PRE_PING", "true").lower() == "true"

        # Query settings
        cls.CLICKHOUSE_QUERY_TIMEOUT = int(os.getenv("CLICKHOUSE_QUERY_TIMEOUT", 300))
        cls.CLICKHOUSE_INSERT_TIMEOUT = int(os.getenv("CLICKHOUSE_INSERT_TIMEOUT", 60))
        cls.CLICKHOUSE_SELECT_TIMEOUT = int(os.getenv("CLICKHOUSE_SELECT_TIMEOUT", 300))
        cls.CLICKHOUSE_MAX_QUERY_SIZE = int(os.getenv("CLICKHOUSE_MAX_QUERY_SIZE", 262144))
        cls.CLICKHOUSE_MAX_RESULT_ROWS = int(os.getenv("CLICKHOUSE_MAX_RESULT_ROWS", 1000000))

        # Performance settings
        cls.CLICKHOUSE_COMPRESSION = os.getenv("CLICKHOUSE_COMPRESSION", "lz4").lower()
        cls.CLICKHOUSE_COMPRESSION_LEVEL = int(os.getenv("CLICKHOUSE_COMPRESSION_LEVEL", 1))
        cls.CLICKHOUSE_INSERT_BATCH_SIZE = int(os.getenv("CLICKHOUSE_INSERT_BATCH_SIZE", 10000))
        cls.CLICKHOUSE_ENABLE_STREAMING = os.getenv("CLICKHOUSE_ENABLE_STREAMING", "true").lower() == "true"
        cls.CLICKHOUSE_BUFFER_SIZE = int(os.getenv("CLICKHOUSE_BUFFER_SIZE", 8192))

        # Caching
        cls.CLICKHOUSE_CACHE_RESULTS = os.getenv("CLICKHOUSE_CACHE_RESULTS", "false").lower() == "true"
        cls.CLICKHOUSE_CACHE_TTL = int(os.getenv("CLICKHOUSE_CACHE_TTL", 300))
        cls.CLICKHOUSE_CACHE_MAX_SIZE = int(os.getenv("CLICKHOUSE_CACHE_MAX_SIZE", 100))

        # Cluster settings
        cls.CLICKHOUSE_CLUSTER_NODES = os.getenv("CLICKHOUSE_CLUSTER_NODES")
        cls.CLICKHOUSE_CLUSTER_NAME = os.getenv("CLICKHOUSE_CLUSTER_NAME")
        cls.CLICKHOUSE_AUTO_FAILOVER = os.getenv("CLICKHOUSE_AUTO_FAILOVER", "true").lower() == "true"
        cls.CLICKHOUSE_LOAD_BALANCING = os.getenv("CLICKHOUSE_LOAD_BALANCING", "round_robin")

        # Monitoring
        cls.CLICKHOUSE_ENABLE_PROFILING = os.getenv("CLICKHOUSE_ENABLE_PROFILING", "false").lower() == "true"
        cls.CLICKHOUSE_LOG_QUERIES = os.getenv("CLICKHOUSE_LOG_QUERIES", "false").lower() == "true"
        cls.CLICKHOUSE_LOG_LEVEL = os.getenv("CLICKHOUSE_LOG_LEVEL", "INFO").upper()
        cls.CLICKHOUSE_METRICS_ENABLED = os.getenv("CLICKHOUSE_METRICS_ENABLED", "false").lower() == "true"

        # Advanced settings
        cls.CLICKHOUSE_READONLY = os.getenv("CLICKHOUSE_READONLY", "false").lower() == "true"
        cls.CLICKHOUSE_EXTREMES = os.getenv("CLICKHOUSE_EXTREMES", "false").lower() == "true"
        cls.CLICKHOUSE_QUOTA_KEY = os.getenv("CLICKHOUSE_QUOTA_KEY")
        cls.CLICKHOUSE_SETTINGS = os.getenv("CLICKHOUSE_SETTINGS")

        # Client settings
        cls.CLICKHOUSE_CLIENT_NAME = os.getenv("CLICKHOUSE_CLIENT_NAME", "python-clickhouse-connector")

    @classmethod
    def get_connection_url(cls) -> str:
        """Build connection URL based on protocol"""
        if cls.CLICKHOUSE_PROTOCOL == "http":
            scheme = "https" if cls.CLICKHOUSE_USE_SSL else "http"
            auth = f"{cls.CLICKHOUSE_USER}:{cls.CLICKHOUSE_PASSWORD}@" if cls.CLICKHOUSE_PASSWORD else f"{cls.CLICKHOUSE_USER}@"
            return f"{scheme}://{auth}{cls.CLICKHOUSE_HOST}:{cls.CLICKHOUSE_PORT}"
        else:
            # Native protocol connection string
            return f"clickhouse://{cls.CLICKHOUSE_USER}:{cls.CLICKHOUSE_PASSWORD}@{cls.CLICKHOUSE_HOST}:{cls.CLICKHOUSE_PORT}/{cls.CLICKHOUSE_DATABASE}"

    @classmethod
    def get_cluster_nodes(cls) -> List[str]:
        """Parse cluster nodes from configuration"""
        if not cls.CLICKHOUSE_CLUSTER_NODES:
            return []
        return [node.strip() for node in cls.CLICKHOUSE_CLUSTER_NODES.split(",")]

    @classmethod
    def get_connection_settings(cls) -> Dict:
        """Get connection-specific settings"""
        settings = {
            'username': cls.CLICKHOUSE_USER,
            'password': cls.CLICKHOUSE_PASSWORD,
            'database': cls.CLICKHOUSE_DATABASE,
            'host': cls.CLICKHOUSE_HOST,
            'port': cls.CLICKHOUSE_PORT,
            'secure': cls.CLICKHOUSE_USE_SSL,
            'compress': cls.CLICKHOUSE_COMPRESSION,
            'client_name': cls.CLICKHOUSE_CLIENT_NAME,
            'send_receive_timeout': cls.CLICKHOUSE_QUERY_TIMEOUT,
        }

        # Add custom settings if provided
        if cls.CLICKHOUSE_SETTINGS:
            try:
                import json
                custom_settings = json.loads(cls.CLICKHOUSE_SETTINGS)
                settings.update(custom_settings)
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON

        return settings
