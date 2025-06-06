"""
Optimized File Service - Business logic for file operations in S3 Sync Service
"""
import os
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from config.settings import settings
from models.s3_models import SyncStatus
from utils.file_utils import FileUtils
from utils.logger import get_logger

logger = get_logger(__name__)


class FileService:
    """Service class for handling file operations"""

    def __init__(self):
        """Initialize file service"""
        self.file_utils = FileUtils()
        logger.info("File Service initialized")

    def download_file_from_s3(self, s3_client, bucket: str, key: str, local_path: str) -> SyncStatus:
        """
        Download a file from S3 to the local filesystem

        Args:
            s3_client: Boto3 S3 client
            bucket: S3 bucket name
            key: S3 object key
            local_path: Local file path

        Returns:
            SyncStatus with operation result
        """
        start_time = time.time()

        try:
            # Check if file should be skipped
            if self._should_skip_download(s3_client, bucket, key, local_path):
                return SyncStatus(
                    operation="skip",
                    file_key=key,
                    status="skipped",
                    message="File already exists and is up to date"
                )

            # Ensure directory structure exists
            if not self.file_utils.ensure_directory_exists(local_path):
                return SyncStatus(
                    operation="download",
                    file_key=key,
                    status="failed",
                    message="Failed to create directory structure"
                )

            # Get file size for validation
            try:
                response = s3_client.head_object(Bucket=bucket, Key=key)
                file_size = response['ContentLength']

                if not settings.is_file_size_allowed(file_size):
                    return SyncStatus(
                        operation="download",
                        file_key=key,
                        status="failed",
                        message=f"File size ({file_size} bytes) exceeds maximum allowed size"
                    )
            except Exception as e:
                logger.warning(f"Could not get file size for {key}: {e}")

            # Download the file
            logger.info(f"Downloading {key} from S3 bucket {bucket} to {local_path}")
            s3_client.download_file(bucket, key, local_path)

            # Verify download if enabled
            if settings.verify_file_integrity:
                if not self._verify_download_integrity(s3_client, bucket, key, local_path):
                    return SyncStatus(
                        operation="download",
                        file_key=key,
                        status="failed",
                        message="File integrity verification failed"
                    )

            duration = time.time() - start_time
            logger.info(f"Successfully downloaded {key} in {duration:.2f} seconds")

            return SyncStatus(
                operation="download",
                file_key=key,
                status="success",
                message=f"Downloaded successfully in {duration:.2f} seconds"
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error downloading file {key}: {error_msg}")

            return SyncStatus(
                operation="download",
                file_key=key,
                status="failed",
                message=f"Download failed: {error_msg}"
            )

    def delete_local_file(self, key: str) -> SyncStatus:
        """
        Delete a file from the local filesystem

        Args:
            key: S3 object key (used to determine local path)

        Returns:
            SyncStatus with operation result
        """
        try:
            local_path = self.file_utils.s3_key_to_local_path(key)

            if self.file_utils.delete_file_safely(local_path):
                # Clean up empty directories
                self.file_utils.cleanup_empty_directories(settings.local_download_dir)

                return SyncStatus(
                    operation="delete",
                    file_key=key,
                    status="success",
                    message="File deleted successfully"
                )
            else:
                return SyncStatus(
                    operation="delete",
                    file_key=key,
                    status="failed",
                    message="File not found or could not be deleted"
                )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error deleting file {key}: {error_msg}")

            return SyncStatus(
                operation="delete",
                file_key=key,
                status="failed",
                message=f"Delete failed: {error_msg}"
            )

    def get_local_file_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a local file

        Args:
            key: S3 object key

        Returns:
            File information dictionary or None if file doesn't exist
        """
        local_path = self.file_utils.s3_key_to_local_path(key)
        return self.file_utils.get_file_info(local_path)

    def list_local_files(self, prefix: str = "") -> List[dict]:
        """
        List all local files with optional prefix filter

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file dictionaries
        """
        files = []

        try:
            base_path = settings.local_download_dir

            for root, _, filenames in os.walk(base_path):
                for filename in filenames:
                    local_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(local_path, base_path)
                    s3_key = relative_path.replace(os.sep, '/')

                    # Apply prefix filter
                    if prefix and not s3_key.startswith(prefix):
                        continue

                    file_info = self.file_utils.get_file_info(local_path)

                    if file_info["exists"]:
                        files.append({
                            'key': s3_key,
                            'size': file_info["size"],
                            'last_modified': datetime.fromtimestamp(file_info["modified_time"]).isoformat(),
                            'etag': file_info["hash"] or "",
                            'local_path': local_path,
                            'content_type': file_info["content_type"]
                        })
        except Exception as e:
            logger.error(f"Error listing local files: {e}")

        return files

    def _should_skip_download(self, s3_client, bucket: str, key: str, local_path: str) -> bool:
        """
        Determine if a file download should be skipped

        Args:
            s3_client: Boto3 S3 client
            bucket: S3 bucket name
            key: S3 object key
            local_path: Local file path

        Returns:
            True if download should be skipped
        """
        if not settings.skip_existing_files:
            return False

        if not os.path.exists(local_path):
            return False

        try:
            # Get S3 object metadata
            s3_response = s3_client.head_object(Bucket=bucket, Key=key)
            s3_size = s3_response['ContentLength']
            s3_etag = s3_response['ETag'].strip('"')

            # Get local file info
            local_size = self.file_utils.get_file_size(local_path)

            # Compare sizes first (quick check)
            if local_size != s3_size:
                return False

            # If integrity verification is enabled, compare hashes
            if settings.verify_file_integrity:
                local_hash = self.file_utils.calculate_file_hash(local_path)
                # Note: S3 ETag is not always MD5, especially for multipart uploads
                # This is a simplified comparison
                if local_hash and local_hash != s3_etag:
                    return False

            logger.debug(f"Skipping download of {key} - file already exists and appears up to date")
            return True

        except Exception as e:
            logger.warning(f"Error checking if download should be skipped for {key}: {e}")
            return False

    def _verify_download_integrity(self, s3_client, bucket: str, key: str, local_path: str) -> bool:
        """
        Verify the integrity of a downloaded file

        Args:
            s3_client: Boto3 S3 client
            bucket: S3 bucket name
            key: S3 object key
            local_path: Local file path

        Returns:
            True if file integrity is verified
        """
        try:
            # Get S3 object metadata
            s3_response = s3_client.head_object(Bucket=bucket, Key=key)
            s3_size = s3_response['ContentLength']

            # Get local file size
            local_size = self.file_utils.get_file_size(local_path)

            # Compare sizes
            if local_size != s3_size:
                logger.error(f"Size mismatch for {key}: S3={s3_size}, Local={local_size}")
                return False

            logger.debug(f"File integrity verified for {key}")
            return True

        except Exception as e:
            logger.error(f"Error verifying file integrity for {key}: {e}")
            return False
