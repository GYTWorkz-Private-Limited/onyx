"""FastAPI application for document indexing."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.config import get_settings
from services.indexing_service import IndexingService
from services.qdrant_service import QdrantService
from models.responses import HealthResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
indexing_service = None
qdrant_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global indexing_service, qdrant_service
    
    settings = get_settings()
    logger.info("Starting Document Indexing API...")
    
    try:
        # Initialize services
        qdrant_service = QdrantService()
        indexing_service = IndexingService()
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.upload_directory, exist_ok=True)
        
        logger.info("Services initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        logger.info("Shutting down Document Indexing API...")


# Create FastAPI application
settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        qdrant_healthy = qdrant_service.health_check() if qdrant_service else False
        
        return HealthResponse(
            status="healthy" if qdrant_healthy else "unhealthy",
            qdrant_connected=qdrant_healthy
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Import and include API routers
from api import collections, indexing, files, search

app.include_router(collections.router, prefix="/collections", tags=["Collections"])
app.include_router(indexing.router, prefix="/index", tags=["Indexing"])
app.include_router(files.router, prefix="/files", tags=["Files"])
app.include_router(search.router, prefix="/search", tags=["Search & Retrieval"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
