"""
Optimized Sync Controller - Streamlined S3 synchronization operations
"""
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from models.s3_models import S3NotificationEvent, HealthCheckResponse
from services.s3_sync_service import S3SyncService
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/sync", tags=["sync"])

# Service instance
sync_service = S3SyncService()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint to verify S3 connectivity"""
    try:
        s3_connection = sync_service.test_s3_connection()
        directory_writable = os.access(settings.local_download_dir, os.W_OK)

        if s3_connection and directory_writable:
            return HealthCheckResponse(
                status="healthy",
                message="S3 Sync Service operational"
            )
        else:
            raise HTTPException(status_code=503, detail="Service unavailable")

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/files")
async def list_files(prefix: str = ""):
    """List files from S3 bucket"""
    try:
        files = sync_service.list_s3_files(prefix)
        return {"files": files, "count": len(files)}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")


@router.post("/trigger")
async def trigger_sync(prefix: str = "", background_tasks: BackgroundTasks = None):
    """Trigger manual sync operation"""
    try:
        logger.info(f"Manual sync triggered with prefix '{prefix}'")

        if background_tasks:
            background_tasks.add_task(sync_service.sync_all_files_from_s3, prefix)
            return {"status": "pending", "message": "Sync started in background"}
        else:
            result = await sync_service.sync_all_files_from_s3(prefix)
            return {"status": "completed", "message": f"Synced {result.processed_files} files"}

    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger sync")


@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file from local cache or S3"""
    try:
        local_path = settings.get_absolute_download_path(file_path)

        # If file doesn't exist locally, download from S3
        if not os.path.exists(local_path):
            logger.info(f"Downloading {file_path} from S3")

            try:
                sync_service.s3_client.head_object(Bucket=settings.s3_bucket_name, Key=file_path)
            except sync_service.s3_client.exceptions.ClientError:
                raise HTTPException(status_code=404, detail="File not found")

            # Download the file
            sync_status = sync_service.file_service.download_file_from_s3(
                sync_service.s3_client,
                settings.s3_bucket_name,
                file_path,
                local_path
            )

            if sync_status.status != "success":
                raise HTTPException(status_code=500, detail="Failed to download file")

        # Return the file
        from utils.file_utils import FileUtils
        content_type = FileUtils.get_file_type(local_path)

        return FileResponse(
            path=local_path,
            filename=os.path.basename(file_path),
            media_type=content_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")


@router.post("/s3-notification")
async def s3_notification(event: S3NotificationEvent, background_tasks: BackgroundTasks):
    """Endpoint for S3 event notifications from AWS Lambda"""
    try:
        logger.info(f"Received S3 notification with {len(event.Records)} records")

        for record in event.Records:
            bucket = record.s3.bucket.name
            key = record.s3.object.key
            event_name = record.eventName

            logger.info(f"Processing S3 event: {event_name} for {bucket}/{key}")

            background_tasks.add_task(
                sync_service.handle_s3_notification,
                bucket,
                key,
                event_name
            )

        return {
            "status": "processing",
            "message": f"Processing {len(event.Records)} S3 events"
        }

    except Exception as e:
        logger.error(f"Error processing S3 notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to process notification")
