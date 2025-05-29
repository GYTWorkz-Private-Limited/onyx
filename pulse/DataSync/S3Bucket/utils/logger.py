"""
Optimized logging configuration for S3 Sync Service
"""
import logging
import sys
from typing import Optional
from config.settings import settings


def setup_logger(name: str = __name__, level: Optional[str] = None) -> logging.Logger:
    """
    Set up and configure logger for the application

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Use settings if not provided
    level = level or settings.log_level

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance with the application's configuration

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return setup_logger(name)
