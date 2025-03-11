"""
Base schemas for API responses.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None 

class SuccessResponse(BaseModel):
    """Standard success response model."""
    success: bool = True
    data: Optional[Dict[str, Any]] = {}
    message: Optional[str] = "Operation completed successfully" 