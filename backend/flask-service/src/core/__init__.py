"""
Core module for Flask service functionality and initialization.
Provides centralized logging, error handling, and configuration.
"""

import logging
import os
import sys
import json
from pathlib import Path

# Try to import shared modules
try:
    from meeting_shared.shared_logging import configure_logging, get_logger
    from meeting_shared.middleware.request_id import RequestIdMiddleware, get_request_id
    SHARED_MODULES_AVAILABLE = True
except ImportError:
    SHARED_MODULES_AVAILABLE = False

# Configure application-wide logging
def setup_logging(log_level=None):
    """
    Configure application-wide logging with appropriate handlers and formatters.
    
    Args:
        log_level: Optional override for log level (default is from environment or INFO)
        
    Returns:
        logging.Logger: Logger instance
    """
    if not log_level:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Use shared logging if available
    if SHARED_MODULES_AVAILABLE:
        # Configure using shared module
        config = {
            'level': log_level,
            'service_name': 'flask-service',
            'json_enabled': os.environ.get('JSON_LOGS', 'true').lower() == 'true',
            'file_enabled': os.environ.get('LOG_TO_FILE', 'false').lower() == 'true',
            'file_path': os.environ.get('LOG_FILE', 'logs/flask-service.log'),
        }
        configure_logging(config)
        logger = get_logger(__name__)
    else:
        # Fall back to basic logging
        logging_format = os.environ.get(
            'LOG_FORMAT', 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        console_formatter = logging.Formatter(logging_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handler if requested
        if os.environ.get('LOG_TO_FILE', 'false').lower() == 'true':
            log_file = os.environ.get('LOG_FILE', 'logs/flask-service.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level))
            file_formatter = logging.Formatter(logging_format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        logger = logging.getLogger(__name__)
    
    logger.info(f"Logging initialized at level {log_level}")
    
    return logger

def log_system_info():
    """
    Log system and environment information for debugging purposes.
    """
    import platform
    import socket
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    # Collect system information
    system_info = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'debug': os.environ.get('DEBUG', 'false').lower() == 'true',
    }
    
    # Log system information
    logger.info(f"System info: {json.dumps(system_info)}")
    
    # Log environment variables (filtered)
    safe_vars = {k: v for k, v in os.environ.items() 
                if not any(secret in k.lower() 
                        for secret in ['key', 'secret', 'token', 'password', 'auth'])}
    
    logger.debug(f"Environment variables: {json.dumps(safe_vars)}")

def log_directory_structure(base_path='/app', max_depth=2):
    """
    Log the directory structure for debugging purposes.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Directory structure of {base_path} (max depth: {max_depth})")
    
    def _log_dir(path, depth=0):
        if depth > max_depth:
            return
        
        try:
            path_obj = Path(path)
            
            # Skip if path doesn't exist
            if not path_obj.exists():
                logger.warning(f"Path does not exist: {path}")
                return
            
            # Log directory entries
            if path_obj.is_dir():
                indent = '  ' * depth
                
                # Get directory contents
                try:
                    contents = list(path_obj.iterdir())
                    
                    # Log count of items
                    logger.info(f"{indent}{path} ({len(contents)} items)")
                    
                    # Sort contents (directories first)
                    contents.sort(key=lambda p: (0 if p.is_dir() else 1, p.name))
                    
                    # Log each item
                    for item in contents:
                        if item.is_dir():
                            _log_dir(item, depth + 1)
                        else:
                            try:
                                stat = item.stat()
                                size_kb = stat.st_size / 1024
                                logger.info(f"{indent}  {item.name} ({size_kb:.1f} KB)")
                            except Exception as e:
                                logger.info(f"{indent}  {item.name} (error: {str(e)})")
                except Exception as e:
                    logger.error(f"Error listing directory {path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error logging directory structure: {str(e)}")
    
    # Start logging directory structure
    _log_dir(base_path)

def register_extensions(app):
    """
    Register Flask extensions with the app.
    
    Args:
        app: Flask application instance
    """
    # Register request ID middleware if available
    if SHARED_MODULES_AVAILABLE:
        RequestIdMiddleware(app)
        app.logger.info("Registered RequestIdMiddleware")

def init_app(app):
    """
    Initialize the Flask application with core functionality.
    
    Args:
        app: Flask application instance
    """
    # Set up logging
    setup_logging()
    
    # Register extensions
    register_extensions(app)
    
    # Log system information
    log_system_info()
    
    # Log directory structure for debugging
    if app.debug:
        log_directory_structure()
    
    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)
    
    app.logger.info("Core initialization complete") 