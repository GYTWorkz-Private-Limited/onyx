"""
S3 Upload Controllers - Business logic for upload operations
"""
from typing import List
from fastapi import UploadFile, HTTPException

from models.upload_models import UploadResponse, HealthCheckResponse
from services.s3_upload_service import S3UploadService
from utils.validators import validate_upload_request
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class UploadController:
    """Controller for handling S3 upload operations"""

    def __init__(self):
        """Initialize the upload controller"""
        self.upload_service = S3UploadService()

    async def health_check(self) -> HealthCheckResponse:
        """
        Perform health check to verify S3 connectivity

        Returns:
            HealthCheckResponse: Health status information
        """
        try:
            self.upload_service.s3_client.head_bucket(Bucket=settings.s3_bucket_name)
            return HealthCheckResponse(
                status="healthy",
                message="S3 Upload Service operational"
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail="Service unavailable")

    async def upload_files(
        self,
        files: List[UploadFile],
        project_name: str,
        s3_prefix: str = ""
    ) -> UploadResponse:
        """
        Upload multiple files to S3 bucket

        Args:
            files: List of files to upload
            project_name: Project folder name
            s3_prefix: Optional S3 prefix path

        Returns:
            UploadResponse: Upload result information
        """
        try:
            logger.info(f"Uploading {len(files)} files to project '{project_name}'")

            # Validate and upload
            validate_upload_request(files, project_name, s3_prefix)
            result = await self.upload_service.upload_multiple_files(files, project_name, s3_prefix)

            logger.info(f"Upload completed: {result.summary}")
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload error: {e}")
            raise HTTPException(status_code=500, detail="Upload failed")