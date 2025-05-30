"""
Optimized S3 Upload Service Server
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from api.routes import router as upload_router
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting S3 Upload Service")
    logger.info(f"Bucket: {settings.s3_bucket_name}, Region: {settings.aws_region}")
    yield
    logger.info("Shutting down S3 Upload Service")


# Create FastAPI application
app = FastAPI(
    title="S3 Upload Service",
    description="Optimized S3 file upload service",
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
app.include_router(upload_router)


@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "service": "S3 Upload Service",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "upload": "/upload/",
            "health": "/upload/health",
            "docs": "/docs"
        }
    }


@app.get("/ping")
async def ping():
    """Simple connectivity test"""
    return {"ping": "pong", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
