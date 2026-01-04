"""
Unified logging configuration with structured output.
"""
import logging
import sys
from typing import Optional
from .config import settings


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    request_id: Optional[str] = None
) -> None:
    """
    Configure unified logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom log format string
        request_id: Optional request ID to include in logs
    """
    level = level or settings.log_level
    format_string = format_string or settings.log_format
    
    # Add request ID to format if provided
    if request_id:
        format_string = f"[{request_id}] {format_string}"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        stream=sys.stdout,
        force=True
    )
    
    # Set specific loggers to avoid noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Initialize logging on module import
setup_logging()
