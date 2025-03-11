"""
Service initialization for the Flask backend.
"""

import logging

logger = logging.getLogger(__name__)

def init_services(app):
    """Initialize all services for the Flask application.
    
    Args:
        app: The Flask application instance
    """
    logger.info("Initializing services")
    
    # You can initialize your services here
    
    logger.info("Services initialized successfully") 