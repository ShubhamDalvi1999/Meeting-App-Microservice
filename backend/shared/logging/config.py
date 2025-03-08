"""
Standardized logging configuration for all backend services.
Supports structured JSON logging and request ID tracking.
"""

import os
import sys
import json
import logging
import logging.config
from datetime import datetime
from functools import partial

# Configure third-party library logging
def configure_library_loggers():
    """Configure third-party library loggers to reduce noise"""
    # Set higher log levels for noisy libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


class RequestIDLogFilter(logging.Filter):
    """Log filter that adds request and correlation IDs to log records."""
    
    def filter(self, record):
        """Add request_id and correlation_id fields to log records."""
        from flask import g, request, has_request_context
        
        # Default values
        record.request_id = "no_request_id"
        record.correlation_id = "no_correlation_id"
        record.user_id = "no_user"
        
        # Add request context if available
        if has_request_context():
            record.request_id = getattr(g, 'request_id', request.headers.get('X-Request-ID', 'no_request_id'))
            record.correlation_id = getattr(g, 'correlation_id', request.headers.get('X-Correlation-ID', 'no_correlation_id'))
            record.user_id = getattr(g, 'user_id', 'anonymous')
            
            # Add request path and method if available
            record.path = request.path
            record.method = request.method
        
        return True


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter that outputs logs in a structured format.
    Includes service name, timestamp, level, message, and additional context.
    """
    
    def __init__(self, service_name=None):
        """
        Initialize the formatter with service name.
        
        Args:
            service_name: Optional service name to include in logs
        """
        super().__init__()
        self.service_name = service_name or os.environ.get('SERVICE_NAME', 'unknown')
    
    def format(self, record):
        """
        Format the log record as a JSON object.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
            
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
            
        if hasattr(record, 'path'):
            log_data['path'] = record.path
            
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 
                           'filename', 'funcName', 'id', 'levelname', 'levelno', 
                           'lineno', 'module', 'msecs', 'message', 'msg', 'name', 
                           'pathname', 'process', 'processName', 'relativeCreated', 
                           'request_id', 'correlation_id', 'stack_info', 'thread', 
                           'threadName', 'user_id', 'path', 'method']:
                if not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data)


def get_log_config(service_name=None, log_level=None, json_logs=True, log_to_file=False, log_file=None):
    """
    Get logging configuration dictionary for a service.
    
    Args:
        service_name: Name of the service for log identification
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to use JSON formatting (default: True)
        log_to_file: Whether to log to a file (default: False)
        log_file: Path to the log file if log_to_file is True
        
    Returns:
        Logging configuration dictionary
    """
    # Default settings
    service_name = service_name or os.environ.get('SERVICE_NAME', 'service')
    log_level = log_level or os.environ.get('LOG_LEVEL', 'INFO')
    json_logs = json_logs if json_logs is not None else (os.environ.get('JSON_LOGS', 'true').lower() == 'true')
    log_to_file = log_to_file if log_to_file is not None else (os.environ.get('LOG_TO_FILE', 'false').lower() == 'true')
    log_file = log_file or os.environ.get('LOG_FILE', f'/app/logs/{service_name}.log')
    
    # Define formatters
    formatters = {
        'json': {
            '()': partial(JSONFormatter, service_name=service_name)
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s [%(request_id)s] [%(correlation_id)s] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    }
    
    # Define handlers
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'json' if json_logs else 'standard',
            'stream': 'ext://sys.stdout'
        }
    }
    
    # Add file handler if enabled
    if log_to_file:
        handlers['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json' if json_logs else 'standard',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        }
    
    # Define filters
    filters = {
        'request_id': {
            '()': RequestIDLogFilter
        }
    }
    
    # Create config dictionary
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'filters': filters,
        'handlers': handlers,
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': ['console'] + (['file'] if log_to_file else []),
                'filters': ['request_id'],
                'propagate': False
            },
            service_name: {
                'level': log_level,
                'handlers': ['console'] + (['file'] if log_to_file else []),
                'filters': ['request_id'],
                'propagate': False
            },
            'werkzeug': {
                'level': 'WARNING',
                'handlers': ['console'] + (['file'] if log_to_file else []),
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': ['console'] + (['file'] if log_to_file else []),
                'propagate': False
            }
        }
    }
    
    return log_config


def setup_logging(app=None, service_name=None, log_level=None, json_logs=True, log_to_file=False, log_file=None):
    """
    Set up logging for a Flask application or globally.
    
    Args:
        app: Optional Flask application instance
        service_name: Name of the service
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to use JSON formatting
        log_to_file: Whether to log to a file
        log_file: Path to the log file if log_to_file is True
    """
    # Configure third-party loggers
    configure_library_loggers()
    
    # Get service name from app if available and not explicitly provided
    if app and not service_name:
        service_name = app.config.get('APP_NAME', app.name)
    
    # Get log level from app if available and not explicitly provided
    if app and not log_level:
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        
    # Get JSON logs setting from app if available
    if app and json_logs is None:
        json_logs = app.config.get('JSON_LOGS', True)
        
    # Get log to file setting from app if available
    if app and log_to_file is None:
        log_to_file = app.config.get('LOG_TO_FILE', False)
        
    # Get log file path from app if available and enabled
    if app and log_to_file and not log_file:
        log_file = app.config.get('LOG_FILE', f'/app/logs/{service_name}.log')
    
    # Get logging config
    log_config = get_log_config(
        service_name=service_name,
        log_level=log_level,
        json_logs=json_logs,
        log_to_file=log_to_file,
        log_file=log_file
    )
    
    # Configure logging
    logging.config.dictConfig(log_config)
    
    # Create a logger for this service
    logger = logging.getLogger(service_name)
    
    # Log startup message
    logger.info(f"Logging initialized for {service_name} at {log_level} level")
    
    return logger 