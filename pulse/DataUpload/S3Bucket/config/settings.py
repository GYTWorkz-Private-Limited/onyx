"""
Optimized Configuration settings for S3 Upload Service
"""
import os
from dotenv import load_dotenv

load_dotenv()


class S3UploadSettings:
    """Streamlined configuration for S3 upload service"""

    def __init__(self):
        # AWS Configuration
        self.aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region: str = os.getenv("AWS_REGION", "us-east-1")
        self.s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "")

        # Upload Configuration
        self.max_concurrent_uploads: int = int(os.getenv("MAX_CONCURRENT_UPLOADS", "5"))
        self.max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
        self.allowed_file_extensions: list = [
            ".txt", ".csv", ".json", ".xlsx", ".pdf",
            ".jpg", ".png", ".docx", ".py", ".zip"
        ]

        # API Configuration
        self.api_port: int = int(os.getenv("API_PORT", "8889"))
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # Validate required settings
        self._validate_settings()

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

    def get_max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024

    def is_file_extension_allowed(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        if not filename:
            return False
        file_extension = os.path.splitext(filename.lower())[1]
        return file_extension in [ext.lower() for ext in self.allowed_file_extensions]


# Global settings instance
settings = S3UploadSettings()
