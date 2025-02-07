import logging
import logging.handlers
import os
from typing import Optional
from pathlib import Path

def setup_logging(
    app_name: str,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the application
    
    Args:
        app_name: Name of the application
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format
        log_file: Path to log file
    """
    # Get configuration from environment or use defaults
    level = getattr(logging, (log_level or os.getenv('LOG_LEVEL', 'INFO')).upper())
    fmt = log_format or os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_path = log_file or os.getenv('LOG_FILE')

    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(level)

    # Create formatters and handlers
    formatter = logging.Formatter(fmt)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log path is specified)
    if log_path:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    logger.info(f"Logging configured for {app_name} at level {level}")
    return logger 