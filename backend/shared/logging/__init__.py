"""
Shared logging module for backend services.
Provides structured JSON logging and request ID tracking.
"""

from .config import (
    setup_logging,
    get_log_config,
    JSONFormatter,
    RequestIDLogFilter,
    configure_library_loggers
)

__all__ = [
    'setup_logging',
    'get_log_config',
    'JSONFormatter',
    'RequestIDLogFilter',
    'configure_library_loggers'
] 