"""
Optimized validation utilities for S3 Upload Service
"""
import os
import re
from typing import List
from fastapi import UploadFile, HTTPException
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_file_size(file: UploadFile) -> None:
    """Validate file size against maximum allowed"""
    max_size = settings.get_max_file_size_bytes()

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File {file.filename} exceeds {settings.max_file_size_mb}MB limit"
        )


def validate_file_extension(filename: str) -> None:
    """Validate file extension against allowed extensions"""
    if not filename or not settings.is_file_extension_allowed(filename):
        ext = os.path.splitext(filename.lower())[1] if filename else "unknown"
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' not allowed"
        )


def validate_filename(filename: str) -> None:
    """Validate filename for security"""
    if not filename or len(filename) > 255:
        raise HTTPException(status_code=400, detail="Invalid filename")

    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in filename for char in dangerous_chars):
        raise HTTPException(status_code=400, detail="Filename contains invalid characters")


def validate_project_name(project_name: str) -> None:
    """Validate project name for S3 compatibility"""
    if not project_name or len(project_name) > 100:
        raise HTTPException(status_code=400, detail="Invalid project name")

    if not re.match(r'^[a-zA-Z0-9._-]+$', project_name):
        raise HTTPException(
            status_code=400,
            detail="Project name can only contain letters, numbers, dots, hyphens, and underscores"
        )


def validate_s3_prefix(s3_prefix: str) -> None:
    """Validate S3 prefix path"""
    if not s3_prefix:
        return

    clean_prefix = s3_prefix.strip('/')
    if not clean_prefix:
        return

    components = clean_prefix.split('/')
    for component in components:
        if not component or not re.match(r'^[a-zA-Z0-9._-]+$', component):
            raise HTTPException(status_code=400, detail="Invalid S3 prefix")


def validate_upload_request(files: List[UploadFile], project_name: str, s3_prefix: str) -> None:
    """Validate complete upload request"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    validate_project_name(project_name)
    validate_s3_prefix(s3_prefix)

    valid_files = 0
    for file in files:
        if file.filename:
            validate_filename(file.filename)
            validate_file_extension(file.filename)
            validate_file_size(file)
            valid_files += 1

    if valid_files == 0:
        raise HTTPException(status_code=400, detail="No valid files found")

    logger.info(f"Validated {valid_files} files for upload to project '{project_name}'")
