from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """Base schema class with common fields and configuration"""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(json_encoders={
        datetime: lambda dt: dt.isoformat()
    })

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error: str
    message: Optional[str] = None
    details: Optional[dict] = None

class SuccessResponse(BaseModel):
    """Standard success response schema"""
    status: str = "success"
    message: Optional[str] = None
    data: Optional[dict] = None 