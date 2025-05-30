"""
S3 Upload API Routes - FastAPI route definitions
"""
from typing import List
from fastapi import APIRouter, UploadFile, File, Form

from models.upload_models import UploadResponse, HealthCheckResponse
from controllers.upload_controller import UploadController
from utils.logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/upload", tags=["upload"])

# Controller instance
upload_controller = UploadController()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint to verify S3 connectivity"""
    return await upload_controller.health_check()


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
    return await upload_controller.upload_files(files, project_name, s3_prefix)
