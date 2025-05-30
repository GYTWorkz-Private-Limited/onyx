"""API package for the File Parser application."""

from .parse_routes import router as parse_router

__all__ = [
    "parse_router",
]
