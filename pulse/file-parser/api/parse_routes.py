"""API routes for file parsing operations."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

from controllers.parse_controller import ParseController
from schemas.parse_schemas import ParserEngine, ParseResponse, ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["parse"])

# Initialize controller
parse_controller = ParseController()


@router.post(
    "/parse/",
    response_model=ParseResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Parse uploaded file",
    description="Parse an uploaded document using either Docling or LlamaParse engine"
)
async def parse_file(
    file: UploadFile = File(..., description="File to parse"),
    engine: ParserEngine = Form(
        default=ParserEngine.LLAMA,
        description="Parser engine to use (docling or llama)"
    )
) -> JSONResponse:
    """
    Parse an uploaded file and return extracted text and markdown.

    - **file**: Upload a supported document file
    - **engine**: Choose between 'docling' (open-source) or 'llama' (cloud-based)

    Returns parsed content with previews and output file paths.
    """
    try:
        result = await parse_controller.parse_file(file, engine)
        return JSONResponse(content=result, status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get(
    "/engines/",
    summary="Get supported parser engines",
    description="Get information about available parser engines and their capabilities"
)
async def get_supported_engines() -> Dict[str, Any]:
    """
    Get information about supported parser engines.

    Returns details about available engines, supported formats, and configuration status.
    """
    try:
        return parse_controller.get_supported_engines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving engine info: {str(e)}")


@router.get(
    "/health/",
    summary="Health check",
    description="Check if the parsing service is healthy"
)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns the status of the parsing service.
    """
    return {
        "status": "healthy",
        "service": "File Parser API",
        "version": "1.0.0"
    }



