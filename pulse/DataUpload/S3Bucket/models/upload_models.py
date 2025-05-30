"""
Optimized Pydantic models for S3 Upload Service
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class UploadFileResult(BaseModel):
    """Individual file upload result"""
    filename: str
    s3_path: str
    status: str  # success/failed
    error: Optional[str] = None
    file_size: Optional[int] = None


class UploadResponse(BaseModel):
    """Upload API response"""
    status: str
    summary: str
    uploaded_files: List[UploadFileResult]
    total_files: int
    successful_uploads: int
    failed_uploads: int
    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
