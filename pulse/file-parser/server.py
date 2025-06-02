"""FastAPI server setup and configuration."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
import logging
import nest_asyncio

try:
    from api.parse_routes import router as parse_router
    PARSE_ROUTES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Parse routes not available: {e}")
    PARSE_ROUTES_AVAILABLE = False
    parse_router = None

from environment import Environment
from utils.output_writer import OutputWriter
from utils.logging_config import setup_logging, get_logger

# Apply nest_asyncio to allow nested event loops (fixes LlamaParse async issues)
nest_asyncio.apply()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger = get_logger(__name__)
    logger.info("🚀 File Parser API starting up...")
    logger.info(f"📁 Output directory: {Environment.get_output_dir()}")
    logger.info(f"📁 Temp directory: {Environment.get_temp_dir()}")
    logger.info(f"🔑 LlamaParse configured: {Environment.validate_llama_config()}")
    logger.info(f"🌐 Server will be available at: http://{Environment.HOST}:{Environment.PORT}")
    logger.info(f"📚 API Documentation: http://localhost:{Environment.PORT}/docs")

    yield

    # Shutdown
    logger.info("🛑 File Parser API shutting down...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)

    app = FastAPI(
        title="File Parser API",
        description="A powerful document parsing service using Docling and LlamaParse",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers if available
    if PARSE_ROUTES_AVAILABLE and parse_router:
        app.include_router(parse_router)
    else:
        # Add basic health endpoint if parse routes are not available
        @app.get("/health")
        async def health():
            return {"status": "healthy", "message": "Basic server running without parse routes"}

    # Ensure output directory exists
    OutputWriter.ensure_output_directory()

    logger.info("FastAPI application created successfully")
    return app


# Create app instance
app = create_app()


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to docs."""
    return RedirectResponse(url="/docs")


# Lifespan events are now handled in the lifespan context manager above


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=Environment.HOST,
        port=Environment.PORT,
        reload=False,
        log_level="warning"
    )
