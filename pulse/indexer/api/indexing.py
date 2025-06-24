"""Indexing endpoints for processing documents."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form

from services.indexing_service import IndexingService
from controllers.indexing_controller import IndexingController
from models.requests import IndexDirectoryRequest, IndexTextRequest, BatchIndexRequest
from models.responses import IndexingResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency to get services and controller
def get_indexing_service() -> IndexingService:
    from main import indexing_service
    if not indexing_service:
        raise HTTPException(status_code=503, detail="Indexing service not available")
    return indexing_service

def get_indexing_controller(indexing_service: IndexingService = Depends(get_indexing_service)) -> IndexingController:
    return IndexingController(indexing_service)


@router.post("/file", response_model=IndexingResponse)
async def index_uploaded_file(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    doc_id: str = Form(None),
    controller: IndexingController = Depends(get_indexing_controller)
):
    """Index an uploaded file."""
    return await controller.index_uploaded_file(file, collection_name, doc_id)


@router.post("/files", response_model=IndexingResponse)
async def index_multiple_files(
    files: List[UploadFile] = File(...),
    collection_name: str = Form(...),
    controller: IndexingController = Depends(get_indexing_controller)
):
    """Index multiple uploaded files."""
    return await controller.index_multiple_files(files, collection_name)


@router.post("/directory", response_model=IndexingResponse)
async def index_directory(
    request: IndexDirectoryRequest,
    controller: IndexingController = Depends(get_indexing_controller)
):
    """Index all files in a directory."""
    return controller.index_directory(request)


@router.post("/text", response_model=IndexingResponse)
async def index_text(
    request: IndexTextRequest,
    controller: IndexingController = Depends(get_indexing_controller)
):
    """Index raw text content."""
    return controller.index_text(request)


@router.post("/batch", response_model=IndexingResponse)
async def index_batch_texts(
    request: BatchIndexRequest,
    controller: IndexingController = Depends(get_indexing_controller)
):
    """Index multiple text contents in batch."""
    return controller.index_batch_texts(request)
