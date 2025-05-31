"""
S3 Sync API Routes - FastAPI route definitions
"""
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse

from models.s3_models import S3NotificationEvent, HealthCheckResponse
from controllers.sync_controller import SyncController
from utils.logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/sync", tags=["sync"])

# Controller instance
sync_controller = SyncController()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint to verify S3 connectivity"""
    return await sync_controller.health_check()


@router.get("/files")
async def list_files(prefix: str = ""):
    """List files from S3 bucket"""
    return await sync_controller.list_files(prefix)


@router.post("/trigger")
async def trigger_sync(prefix: str = "", background_tasks: BackgroundTasks = None):
    """Trigger manual sync operation"""
    return await sync_controller.trigger_sync(prefix, background_tasks)


@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file from local cache or S3"""
    return await sync_controller.download_file(file_path)


@router.post("/s3-notification")
async def s3_notification(event: S3NotificationEvent, background_tasks: BackgroundTasks):
    """Endpoint for S3 event notifications from AWS Lambda"""
    return await sync_controller.handle_s3_notification_endpoint(event, background_tasks)
