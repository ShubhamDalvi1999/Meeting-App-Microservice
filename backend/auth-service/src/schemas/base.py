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