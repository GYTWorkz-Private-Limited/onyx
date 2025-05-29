"""
Optimized S3 Sync Service Server
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from controllers.sync_controller import router as sync_router
from services.s3_sync_service import S3SyncService
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Global service instance
sync_service = None
periodic_sync_task = None


async def periodic_sync():
    """Periodically sync all files from S3"""
    global sync_service

    while True:
        try:
            if settings.enable_periodic_sync:
                logger.info("Starting periodic sync")
                await sync_service.sync_all_files_from_s3()
                logger.info(f"Periodic sync completed. Next sync in {settings.sync_interval_hours} hours")

            await asyncio.sleep(settings.get_sync_interval_seconds())

        except asyncio.CancelledError:
            logger.info("Periodic sync task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in periodic sync: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan manager"""
    global sync_service, periodic_sync_task

    logger.info("Starting S3 Sync Service")
    logger.info(f"Bucket: {settings.s3_bucket_name}, Region: {settings.aws_region}")

    try:
        # Initialize sync service
        sync_service = S3SyncService()

        # Perform initial sync
        logger.info("Performing initial sync from S3")
        await sync_service.sync_all_files_from_s3()

        # Start periodic sync if enabled
        if settings.enable_periodic_sync:
            logger.info("Starting periodic sync task")
            periodic_sync_task = asyncio.create_task(periodic_sync())

        logger.info("S3 Sync Service startup completed")

    except Exception as e:
        logger.error(f"Failed to start S3 Sync Service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down S3 Sync Service")

    if periodic_sync_task:
        periodic_sync_task.cancel()
        try:
            await periodic_sync_task
        except asyncio.CancelledError:
            logger.info("Periodic sync task cancelled")

    logger.info("S3 Sync Service shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="S3 Sync Service",
    description="Optimized S3 file synchronization service",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sync_router)


@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "service": "S3 Sync Service",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/sync/health",
            "files": "/sync/files",
            "download": "/sync/download/{file_path}",
            "trigger_sync": "/sync/trigger",
            "s3_notification": "/sync/s3-notification",
            "docs": "/docs"
        }
    }


@app.get("/ping")
async def ping():
    """Simple connectivity test"""
    return {"ping": "pong", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    logger.info(f"Starting S3 Sync Service on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
