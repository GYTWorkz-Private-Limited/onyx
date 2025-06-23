"""File upload and management endpoints."""

import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends

from services.config import get_settings
from controllers.files_controller import FilesController
from models.responses import FileUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()

def get_settings_dep():
    return get_settings()

def get_files_controller(settings = Depends(get_settings_dep)) -> FilesController:
    return FilesController(settings)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    controller: FilesController = Depends(get_files_controller)
):
    """Upload a single file."""
    return await controller.upload_file(file)


@router.post("/upload-multiple", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    controller: FilesController = Depends(get_files_controller)
):
    """Upload multiple files."""
    return await controller.upload_multiple_files(files)


@router.get("/list", response_model=List[dict])
async def list_uploaded_files(controller: FilesController = Depends(get_files_controller)):
    """List all uploaded files."""
    return controller.list_uploaded_files()


@router.delete("/{filename}", response_model=dict)
async def delete_file(filename: str, controller: FilesController = Depends(get_files_controller)):
    """Delete an uploaded file."""
    return controller.delete_file(filename)
