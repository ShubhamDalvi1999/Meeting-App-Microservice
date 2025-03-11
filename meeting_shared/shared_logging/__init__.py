"""
Shared logging module for backend services.
Provides structured JSON logging and request ID tracking.
"""

# Import standard logging to ensure it's fully initialized
import logging

# Define exports without importing from config.py
__all__ = [
    'setup_logging',
    'get_log_config',
    'JSONFormatter',
    'RequestIDLogFilter',
    'configure_library_loggers'
]

# Define a simple setup_logging function that can be used as a fallback
def setup_logging(app=None, service_name=None, log_level=None, json_logs=True, log_to_file=False, log_file=None):
    """
    Simple fallback logging setup function.
    The real implementation is in config.py
    """
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Try to import the real setup_logging function
    try:
        from .config import setup_logging as real_setup_logging
        return real_setup_logging(app, service_name, log_level, json_logs, log_to_file, log_file)
    except ImportError:
        logging.warning("Could not import logging config module. Using basic logging setup.")
        return None 