"""
Base schemas for API responses.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel

class BaseSchema(BaseModel):
    """Base schema that all other schemas should inherit from."""
    class Config:
        orm_mode = True
        validate_assignment = True
        arbitrary_types_allowed = True
        extra = "forbid"

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