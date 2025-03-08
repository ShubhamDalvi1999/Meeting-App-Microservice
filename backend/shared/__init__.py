"""
Shared modules package for backend services.
Provides consistent import mechanisms across different services.
"""

import os
import sys
import importlib
import logging

logger = logging.getLogger(__name__)

# Define potential module paths
POTENTIAL_PATHS = [
    '/app',
    '/app/shared',
    '/app/backend/shared',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Project root
    os.path.dirname(os.path.abspath(__file__)),  # Shared module directory
]

# Add paths to sys.path if not already present
for path in POTENTIAL_PATHS:
    if path not in sys.path and os.path.exists(path):
        sys.path.append(path)
        logger.debug(f"Added {path} to sys.path")

# Helper function to import a module with fallbacks
def import_module(module_name, package=None):
    """
    Import a module with fallbacks.
    
    Args:
        module_name: The name of the module to import
        package: The package to import from (optional)
        
    Returns:
        The imported module, or None if not found
    """
    # Try different import paths
    possible_imports = [
        module_name,  # Direct import
        f"shared.{module_name}",  # From shared package
        f"backend.shared.{module_name}",  # From backend.shared package
    ]
    
    if package:
        possible_imports.extend([
            f"{package}.{module_name}",
            f"shared.{package}.{module_name}",
            f"backend.shared.{package}.{module_name}",
        ])
    
    for import_path in possible_imports:
        try:
            return importlib.import_module(import_path)
        except ImportError:
            continue
    
    return None

# Import key shared modules with fallbacks
try:
    # Import logging module
    logging_module = import_module('logging')
    
    # Import middleware modules
    middleware_module = import_module('middleware')
    request_id_module = import_module('request_id', 'middleware')
    
    # Import database modules
    database_module = import_module('database')
    
    # Import utils modules
    utils_module = import_module('utils')
    http_module = import_module('http', 'utils')
    
    # Import config
    config_module = import_module('config')
    
    IMPORTS_SUCCESSFUL = True
except Exception as e:
    IMPORTS_SUCCESSFUL = False
    logger.error(f"Error importing shared modules: {e}")

# Define public exports
__all__ = [
    'import_module',
    'logging_module',
    'middleware_module',
    'request_id_module',
    'database_module',
    'utils_module',
    'http_module',
    'config_module',
] 