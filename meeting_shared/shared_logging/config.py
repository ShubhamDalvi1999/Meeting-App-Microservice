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

# Try to import sampling module
try:
    from .sampling import SamplingLogFilter, SamplingConfig
    HAS_SAMPLING = True
except ImportError:
    HAS_SAMPLING = False

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
        # Import Flask modules inside the method to avoid circular imports
        try:
            # Dynamically import Flask to avoid circular imports
            from flask import g, request, has_request_context
            
            # Default values
            record.request_id = "no_request_id"
            record.correlation_id = "no_correlation_id"
            record.user_id = "no_user"
            record.path = "/"
            record.method = "NONE"
            
            # Add request context if available
            if has_request_context():
                record.request_id = getattr(g, 'request_id', request.headers.get('X-Request-ID', 'no_request_id'))
                record.correlation_id = getattr(g, 'correlation_id', request.headers.get('X-Correlation-ID', 'no_correlation_id'))
                record.user_id = getattr(g, 'user_id', 'anonymous')
                record.path = request.path
                record.method = request.method
        except (ImportError, RuntimeError):
            # If Flask is not available or not in request context, use default values
            record.request_id = "no_request_id"
            record.correlation_id = "no_correlation_id"
            record.user_id = "no_user"
            record.path = "/"
            record.method = "NONE"
        
        # Add taskName attribute if missing
        if not hasattr(record, 'taskName'):
            record.taskName = None
            
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
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                          'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                          'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                          'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName',
                          'request_id', 'correlation_id', 'user_id', 'path', 'method']:
                log_data[key] = value
        
        return json.dumps(log_data)


def get_log_config(service_name=None, log_level=None, json_logs=True, log_to_file=False, log_file=None, enable_sampling=False, sampling_config=None):
    """
    Get logging configuration dictionary.
    
    Args:
        service_name: Service name for logs
        log_level: Log level (DEBUG, INFO, etc.)
        json_logs: Whether to use JSON formatting
        log_to_file: Whether to log to a file
        log_file: Log file path
        enable_sampling: Whether to enable log sampling
        sampling_config: Sampling configuration
        
    Returns:
        Logging configuration dictionary
    """
    # Set defaults
    service_name = service_name or os.environ.get('SERVICE_NAME', 'app')
    log_level = log_level or os.environ.get('LOG_LEVEL', 'INFO').upper()
    json_logs = json_logs if json_logs is not None else os.environ.get('JSON_LOGS', 'true').lower() == 'true'
    log_to_file = log_to_file if log_to_file is not None else os.environ.get('LOG_TO_FILE', 'false').lower() == 'true'
    log_file = log_file or os.environ.get('LOG_FILE', f'logs/{service_name}.log')
    enable_sampling = enable_sampling if enable_sampling is not None else os.environ.get('ENABLE_LOG_SAMPLING', 'false').lower() == 'true'
    
    # Define formatters
    formatters = {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            '()': JSONFormatter,
            'service_name': service_name
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
    
    # Add sampling filter if enabled
    if enable_sampling and HAS_SAMPLING:
        filters['sampling'] = {
            '()': SamplingLogFilter
        }
    
    # Create filter list
    filter_list = ['request_id']
    if enable_sampling and HAS_SAMPLING:
        filter_list.append('sampling')
    
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
                'filters': filter_list,
                'propagate': False
            },
            service_name: {
                'level': log_level,
                'handlers': ['console'] + (['file'] if log_to_file else []),
                'filters': filter_list,
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


def setup_logging(app=None, service_name=None, log_level=None, json_logs=True, log_to_file=False, log_file=None, enable_sampling=False, sampling_config=None):
    """
    Set up logging configuration.
    
    Args:
        app: Flask application (optional)
        service_name: Service name for logs
        log_level: Log level (DEBUG, INFO, etc.)
        json_logs: Whether to use JSON formatting
        log_to_file: Whether to log to a file
        log_file: Log file path
        enable_sampling: Whether to enable log sampling
        sampling_config: Sampling configuration
        
    Returns:
        Configured logger
    """
    # Get service name from app if available
    if app and not service_name:
        service_name = app.name
    
    # Get log level from app if available
    if app and not log_level:
        log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    # Get log config
    log_config = get_log_config(
        service_name=service_name,
        log_level=log_level,
        json_logs=json_logs,
        log_to_file=log_to_file,
        log_file=log_file,
        enable_sampling=enable_sampling,
        sampling_config=sampling_config
    )
    
    # Configure logging
    logging.config.dictConfig(log_config)
    
    # Configure sampling if enabled
    if enable_sampling and HAS_SAMPLING and sampling_config:
        from .sampling import configure_sampling
        configure_sampling(sampling_config)
    
    # Configure library loggers
    configure_library_loggers()
    
    # Get logger for service
    logger = logging.getLogger(service_name)
    
    # Log startup message
    logger.info(f"Logging configured for {service_name} at level {log_level}")
    
    return logger 