import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration for MongoDB database connection"""
    MONGO_HOST = None
    MONGO_PORT = 27017
    MONGO_USERNAME = None
    MONGO_PASSWORD = None
    MONGO_DB = None
    MONGO_AUTH_SOURCE = None
    MONGO_REPLICA_SET = None

    # SSL/TLS Configuration
    MONGO_USE_SSL = False
    MONGO_SSL_CERT_REQS = None
    MONGO_SSL_CA_CERTS = None
    MONGO_SSL_CERTFILE = None
    MONGO_SSL_KEYFILE = None

    # Connection Pool Configuration
    MONGO_MAX_POOL_SIZE = 100
    MONGO_MIN_POOL_SIZE = 0
    MONGO_MAX_IDLE_TIME_MS = 30000
    MONGO_WAIT_QUEUE_TIMEOUT_MS = 5000
    MONGO_CONNECT_TIMEOUT_MS = 20000
    MONGO_SERVER_SELECTION_TIMEOUT_MS = 30000
    MONGO_SOCKET_TIMEOUT_MS = 20000
    MONGO_HEARTBEAT_FREQUENCY_MS = 10000

    # Connection String (alternative to individual parameters)
    MONGO_URI = None

    @classmethod
    def validate(cls):
        """Load and validate environment variables"""
        # Check if URI is provided (takes precedence)
        cls.MONGO_URI = os.getenv("MONGO_URI")

        if cls.MONGO_URI:
            # If URI is provided, extract database name from URI
            cls._extract_db_from_uri()
            cls._load_optional_config()
            return

        # Required variables when not using URI
        required_vars = {
            'MONGO_HOST': os.getenv("MONGO_HOST"),
            'MONGO_DB': os.getenv("MONGO_DB")
        }

        # Set values and check for missing variables
        missing = []
        for key, value in required_vars.items():
            setattr(cls, key, value)
            if value is None:
                missing.append(key)

        if missing:
            raise ValueError(f"Missing required config variables: {', '.join(missing)}. "
                           f"Either provide MONGO_URI or individual connection parameters.")

        # Optional connection parameters
        cls.MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
        cls.MONGO_USERNAME = os.getenv("MONGO_USERNAME")
        cls.MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
        cls.MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", "admin")
        cls.MONGO_REPLICA_SET = os.getenv("MONGO_REPLICA_SET")

        cls._load_optional_config()

    @classmethod
    def _extract_db_from_uri(cls):
        """Extract database name from MongoDB URI"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(cls.MONGO_URI)

            # Extract database name from path (remove leading slash)
            if parsed.path and len(parsed.path) > 1:
                # Handle case where path might have query parameters
                db_name = parsed.path[1:].split('?')[0]
                cls.MONGO_DB = db_name
            else:
                # If no database in URI, use default
                cls.MONGO_DB = "test"

        except Exception as e:
            # Fallback to default database name
            cls.MONGO_DB = "test"

    @classmethod
    def _load_optional_config(cls):
        """Load optional configuration parameters"""
        # SSL Configuration
        cls.MONGO_USE_SSL = os.getenv("MONGO_USE_SSL", "false").lower() == "true"
        cls.MONGO_SSL_CERT_REQS = os.getenv("MONGO_SSL_CERT_REQS")
        cls.MONGO_SSL_CA_CERTS = os.getenv("MONGO_SSL_CA_CERTS")
        cls.MONGO_SSL_CERTFILE = os.getenv("MONGO_SSL_CERTFILE")
        cls.MONGO_SSL_KEYFILE = os.getenv("MONGO_SSL_KEYFILE")

        # Connection Pool Configuration
        cls.MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", 100))
        cls.MONGO_MIN_POOL_SIZE = int(os.getenv("MONGO_MIN_POOL_SIZE", 0))
        cls.MONGO_MAX_IDLE_TIME_MS = int(os.getenv("MONGO_MAX_IDLE_TIME_MS", 30000))
        cls.MONGO_WAIT_QUEUE_TIMEOUT_MS = int(os.getenv("MONGO_WAIT_QUEUE_TIMEOUT_MS", 5000))
        cls.MONGO_CONNECT_TIMEOUT_MS = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", 20000))
        cls.MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", 30000))
        cls.MONGO_SOCKET_TIMEOUT_MS = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", 20000))
        cls.MONGO_HEARTBEAT_FREQUENCY_MS = int(os.getenv("MONGO_HEARTBEAT_FREQUENCY_MS", 10000))

    @classmethod
    def get_connection_string(cls):
        """Build MongoDB connection string"""
        if cls.MONGO_URI:
            return cls.MONGO_URI

        # Build connection string from individual parameters
        auth_part = ""
        if cls.MONGO_USERNAME and cls.MONGO_PASSWORD:
            auth_part = f"{cls.MONGO_USERNAME}:{cls.MONGO_PASSWORD}@"

        host_part = f"{cls.MONGO_HOST}:{cls.MONGO_PORT}"

        # Handle replica set
        if cls.MONGO_REPLICA_SET:
            host_part += f"/?replicaSet={cls.MONGO_REPLICA_SET}"

        connection_string = f"mongodb://{auth_part}{host_part}/{cls.MONGO_DB}"

        # Add auth source if specified
        if cls.MONGO_AUTH_SOURCE and cls.MONGO_USERNAME:
            separator = "&" if "?" in connection_string else "?"
            connection_string += f"{separator}authSource={cls.MONGO_AUTH_SOURCE}"

        return connection_string

    @classmethod
    def get_client_options(cls):
        """Get PyMongo client options"""
        options = {
            'maxPoolSize': cls.MONGO_MAX_POOL_SIZE,
            'minPoolSize': cls.MONGO_MIN_POOL_SIZE,
            'maxIdleTimeMS': cls.MONGO_MAX_IDLE_TIME_MS,
            'waitQueueTimeoutMS': cls.MONGO_WAIT_QUEUE_TIMEOUT_MS,
            'connectTimeoutMS': cls.MONGO_CONNECT_TIMEOUT_MS,
            'serverSelectionTimeoutMS': cls.MONGO_SERVER_SELECTION_TIMEOUT_MS,
            'socketTimeoutMS': cls.MONGO_SOCKET_TIMEOUT_MS,
            'heartbeatFrequencyMS': cls.MONGO_HEARTBEAT_FREQUENCY_MS,
        }

        # Add SSL options if enabled
        if cls.MONGO_USE_SSL:
            options['ssl'] = True
            if cls.MONGO_SSL_CERT_REQS:
                options['ssl_cert_reqs'] = cls.MONGO_SSL_CERT_REQS
            if cls.MONGO_SSL_CA_CERTS:
                options['ssl_ca_certs'] = cls.MONGO_SSL_CA_CERTS
            if cls.MONGO_SSL_CERTFILE:
                options['ssl_certfile'] = cls.MONGO_SSL_CERTFILE
            if cls.MONGO_SSL_KEYFILE:
                options['ssl_keyfile'] = cls.MONGO_SSL_KEYFILE

        return options
