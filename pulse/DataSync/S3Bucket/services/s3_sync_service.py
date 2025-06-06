"""
Optimized S3 Sync Service - Business logic for S3 synchronization operations
"""
import boto3
import time
from typing import List, Optional
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

from config.settings import settings
from models.s3_models import SyncResponse, SyncStatus
from services.file_service import FileService
from utils.logger import get_logger

logger = get_logger(__name__)


class S3SyncService:
    """Service class for handling S3 synchronization operations"""

    def __init__(self):
        """Initialize S3 sync service"""
        self.s3_client = self._create_s3_client()
        self.file_service = FileService()
        self.last_sync_time: Optional[datetime] = None
        logger.info("S3 Sync Service initialized")

    def _create_s3_client(self):
        """Create and configure S3 client"""
        try:
            client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )

            # Test connection by checking bucket access
            client.head_bucket(Bucket=settings.s3_bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {settings.s3_bucket_name}")
            return client

        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise ValueError("AWS credentials not configured properly")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket not found: {settings.s3_bucket_name}")
                raise ValueError(f"S3 bucket '{settings.s3_bucket_name}' does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket: {settings.s3_bucket_name}")
                raise ValueError(f"Access denied to S3 bucket '{settings.s3_bucket_name}'")
            else:
                logger.error(f"Error connecting to S3: {e}")
                raise ValueError(f"Failed to connect to S3: {e}")

    def list_s3_files(self, prefix: str = "") -> List[dict]:
        """
        List files in the S3 bucket with the given prefix

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file dictionaries
        """
        try:
            files = []
            paginator = self.s3_client.get_paginator('list_objects_v2')

            page_iterator = paginator.paginate(
                Bucket=settings.s3_bucket_name,
                Prefix=prefix
            )

            for page in page_iterator:
                if 'Contents' in page:
                    for item in page['Contents']:
                        files.append({
                            'key': item['Key'],
                            'size': item['Size'],
                            'last_modified': item['LastModified'].isoformat(),
                            'etag': item['ETag'].strip('"')
                        })

            logger.info(f"Found {len(files)} files in S3 with prefix '{prefix}'")
            return files

        except Exception as e:
            logger.error(f"Error listing S3 files: {e}")
            return []

    async def sync_all_files_from_s3(self, prefix: str = "") -> SyncResponse:
        """
        Sync all files from S3 to local filesystem

        Args:
            prefix: Optional prefix to filter files

        Returns:
            SyncResponse with detailed results
        """
        start_time = time.time()
        logger.info(f"Starting full sync from S3 with prefix '{prefix}'")

        try:
            # Get list of files in S3
            s3_files = self.list_s3_files(prefix)

            if not s3_files:
                return SyncResponse(
                    status="success",
                    message="No files found in S3 to sync",
                    processed_files=0,
                    successful_operations=0,
                    failed_operations=0,
                    sync_details=[]
                )

            # Process each file
            sync_details = []
            successful_operations = 0
            failed_operations = 0

            for file_info in s3_files:
                local_path = settings.get_absolute_download_path(file_info['key'])

                # Download file
                sync_status = self.file_service.download_file_from_s3(
                    self.s3_client,
                    settings.s3_bucket_name,
                    file_info['key'],
                    local_path
                )

                sync_details.append(sync_status)

                if sync_status.status == "success":
                    successful_operations += 1
                elif sync_status.status == "failed":
                    failed_operations += 1
                # Note: skipped files are not counted as failures

            # Update last sync time
            self.last_sync_time = datetime.now()

            duration = time.time() - start_time
            total_files = len(s3_files)

            # Determine overall status
            if failed_operations == 0:
                overall_status = "success"
            elif successful_operations > 0:
                overall_status = "partial_success"
            else:
                overall_status = "failed"

            message = f"Synced {successful_operations} of {total_files} files in {duration:.2f} seconds"
            if failed_operations > 0:
                message += f" ({failed_operations} failed)"

            logger.info(f"Sync completed: {message}")

            return SyncResponse(
                status=overall_status,
                message=message,
                processed_files=total_files,
                successful_operations=successful_operations,
                failed_operations=failed_operations,
                sync_details=sync_details
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error during sync operation: {error_msg}")

            return SyncResponse(
                status="failed",
                message=f"Sync failed: {error_msg}",
                processed_files=0,
                successful_operations=0,
                failed_operations=1,
                sync_details=[
                    SyncStatus(
                        operation="error",
                        file_key="",
                        status="failed",
                        message=error_msg
                    )
                ]
            )

    async def handle_s3_notification(self, bucket: str, key: str, event_name: str) -> SyncStatus:
        """
        Handle individual S3 notification event

        Args:
            bucket: S3 bucket name
            key: S3 object key
            event_name: S3 event name

        Returns:
            SyncStatus with operation result
        """
        logger.info(f"Processing S3 event: {event_name} for {bucket}/{key}")

        try:
            if event_name.startswith('ObjectCreated:'):
                # File was created or updated - download it
                local_path = settings.get_absolute_download_path(key)
                return self.file_service.download_file_from_s3(
                    self.s3_client, bucket, key, local_path
                )

            elif event_name.startswith('ObjectRemoved:'):
                # File was deleted - remove local copy
                return self.file_service.delete_local_file(key)

            else:
                logger.warning(f"Unknown event type: {event_name}")
                return SyncStatus(
                    operation="error",
                    file_key=key,
                    status="failed",
                    message=f"Unknown event type: {event_name}"
                )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error handling S3 notification for {key}: {error_msg}")

            return SyncStatus(
                operation="error",
                file_key=key,
                status="failed",
                message=f"Notification handling failed: {error_msg}"
            )



    def test_s3_connection(self) -> bool:
        """
        Test S3 connection

        Returns:
            True if connection is successful
        """
        try:
            self.s3_client.head_bucket(Bucket=settings.s3_bucket_name)
            return True
        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
            return False
