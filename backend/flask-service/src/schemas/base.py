"""
This module re-exports the shared schema base classes to maintain
backward compatibility with code that imports from here.
"""

from meeting_shared.schemas.base import ErrorResponse
from pydantic import BaseModel as SharedBaseSchema
from typing import Optional, Dict, Any

# Define a SuccessResponse class for backward compatibility
class SuccessResponse(dict):
    """Standard success response model."""
    def __init__(self, data=None, message=None):
        super().__init__(
            success=True,
            data=data or {},
            message=message or "Operation completed successfully"
        )

# For backward compatibility, provide a marshmallow-based BaseSchema
from marshmallow import Schema, fields, EXCLUDE

class BaseSchema(Schema):
    """Base schema class with common configuration."""
    
    class Meta:
        unknown = EXCLUDE
        ordered = True

    id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def __init__(self, *args, **kwargs):
        """Initialize schema with strict validation by default."""
        kwargs['strict'] = kwargs.get('strict', True)
        super().__init__(*args, **kwargs) 