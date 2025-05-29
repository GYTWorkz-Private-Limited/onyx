"""
Optimized Configuration settings for S3 Sync Service
"""
import os
from dotenv import load_dotenv

load_dotenv()


class S3SyncSettings:
    """Streamlined configuration for S3 sync service"""

    def __init__(self):
        # AWS Configuration
        self.aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region: str = os.getenv("AWS_REGION", "us-east-1")
        self.s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "")

        # Sync Configuration
        self.local_download_dir: str = os.getenv("LOCAL_DOWNLOAD_DIR", "downloaded_files")
        self.sync_interval_hours: float = float(os.getenv("SYNC_INTERVAL_HOURS", "1.0"))
        self.enable_periodic_sync: bool = os.getenv("ENABLE_PERIODIC_SYNC", "true").lower() == "true"
        self.max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "500"))

        # API Configuration
        self.api_port: int = int(os.getenv("API_PORT", "8888"))
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # File Processing Configuration
        self.skip_existing_files: bool = os.getenv("SKIP_EXISTING_FILES", "true").lower() == "true"
        self.verify_file_integrity: bool = os.getenv("VERIFY_FILE_INTEGRITY", "false").lower() == "true"

        # Validate required settings
        self._validate_settings()

        # Ensure download directory exists
        self._ensure_download_directory()

    def _validate_settings(self):
        """Validate required AWS configuration"""
        required = [
            ("AWS_ACCESS_KEY_ID", self.aws_access_key_id),
            ("AWS_SECRET_ACCESS_KEY", self.aws_secret_access_key),
            ("S3_BUCKET_NAME", self.s3_bucket_name),
        ]

        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        if self.sync_interval_hours <= 0:
            raise ValueError("SYNC_INTERVAL_HOURS must be greater than 0")

    def _ensure_download_directory(self):
        """Ensure the download directory exists"""
        try:
            os.makedirs(self.local_download_dir, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Failed to create download directory '{self.local_download_dir}': {e}")

    def get_max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024

    def get_sync_interval_seconds(self) -> float:
        """Get sync interval in seconds"""
        return self.sync_interval_hours * 3600

    def get_absolute_download_path(self, relative_path: str) -> str:
        """Get absolute path for a file in the download directory"""
        return os.path.join(self.local_download_dir, relative_path)

    def is_file_size_allowed(self, file_size: int) -> bool:
        """Check if file size is within allowed limits"""
        return file_size <= self.get_max_file_size_bytes()


# Global settings instance
settings = S3SyncSettings()
