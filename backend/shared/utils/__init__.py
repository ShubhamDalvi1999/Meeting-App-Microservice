"""
Shared utilities module for backend services.
Provides common utilities for HTTP requests, date handling, and more.
"""

# Import commonly used utilities for easier access
try:
    from .http import (
        get, post, put, delete, patch,
        make_request, add_request_id_headers
    )
except ImportError:
    pass 