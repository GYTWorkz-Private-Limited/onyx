"""
Optimized Upload Controller - Streamlined S3 file upload operations
"""
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from models.upload_models import UploadResponse, HealthCheckResponse
from services.s3_upload_service import S3UploadService
from utils.validators import validate_upload_request
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/upload", tags=["upload"])

# Service instance
upload_service = S3UploadService()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint to verify S3 connectivity"""
    try:
        upload_service.s3_client.head_bucket(Bucket=settings.s3_bucket_name)
        return HealthCheckResponse(
            status="healthy",
            message="S3 Upload Service operational"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.post("/", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    project_name: str = Form(...),
    s3_prefix: str = Form("")
):
    """
    Upload files to S3 bucket with concurrent processing

    Args:
        files: Files to upload
        project_name: Project folder name
        s3_prefix: Optional S3 prefix path
    """
    try:
        logger.info(f"Uploading {len(files)} files to project '{project_name}'")

        # Validate and upload
        validate_upload_request(files, project_name, s3_prefix)
        result = await upload_service.upload_multiple_files(files, project_name, s3_prefix)

        logger.info(f"Upload completed: {result.summary}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")
