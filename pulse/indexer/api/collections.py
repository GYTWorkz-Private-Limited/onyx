"""Collection management endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Depends

from services.qdrant_service import QdrantService
from services.indexing_service import IndexingService
from controllers.collections_controller import CollectionsController
from models.requests import CreateCollectionRequest
from models.responses import CollectionInfo, CollectionListResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependencies to get services and controller
def get_qdrant_service() -> QdrantService:
    from main import qdrant_service
    if not qdrant_service:
        raise HTTPException(status_code=503, detail="Qdrant service not available")
    return qdrant_service

def get_indexing_service() -> IndexingService:
    from main import indexing_service
    if not indexing_service:
        raise HTTPException(status_code=503, detail="Indexing service not available")
    return indexing_service

def get_collections_controller(
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    indexing_service: IndexingService = Depends(get_indexing_service)
) -> CollectionsController:
    return CollectionsController(qdrant_service, indexing_service)


@router.get("/", response_model=CollectionListResponse)
async def list_collections(controller: CollectionsController = Depends(get_collections_controller)):
    """List all collections."""
    return controller.list_collections()


@router.get("/{collection_name}", response_model=CollectionInfo)
async def get_collection_info(
    collection_name: str,
    controller: CollectionsController = Depends(get_collections_controller)
):
    """Get information about a specific collection."""
    return controller.get_collection_info(collection_name)


@router.post("/{collection_name}", response_model=dict)
async def create_collection(
    collection_name: str,
    request: CreateCollectionRequest,
    controller: CollectionsController = Depends(get_collections_controller)
):
    """Create a new collection."""
    return controller.create_collection(collection_name, request)


@router.delete("/{collection_name}", response_model=dict)
async def delete_collection(
    collection_name: str,
    controller: CollectionsController = Depends(get_collections_controller)
):
    """Delete a collection."""
    return controller.delete_collection(collection_name)


@router.put("/{collection_name}/recreate", response_model=dict)
async def recreate_collection(
    collection_name: str,
    request: CreateCollectionRequest,
    controller: CollectionsController = Depends(get_collections_controller)
):
    """Recreate a collection (delete and create new)."""
    return controller.recreate_collection(collection_name, request)
