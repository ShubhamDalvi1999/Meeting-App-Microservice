from datetime import datetime
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.inspection import inspect
from ..database import db, transaction

T = TypeVar('T', bound=BaseModel)

class BaseModelMixin:
    """Base model mixin with enhanced schema conversion methods"""
    
    @classmethod
    def from_schema(cls, schema: BaseModel, **kwargs) -> 'BaseModelMixin':
        """
        Create a new model instance from a Pydantic schema
        
        Args:
            schema: Pydantic schema instance
            **kwargs: Additional fields to set on the model
        """
        schema_dict = schema.model_dump(exclude_unset=True)
        schema_dict.update(kwargs)
        
        # Filter out fields that don't exist in the model
        model_fields = {c.key for c in inspect(cls).columns}
        filtered_dict = {k: v for k, v in schema_dict.items() if k in model_fields}
        
        return cls(**filtered_dict)
    
    def update_from_schema(self, schema: BaseModel, exclude_fields: Optional[set] = None) -> None:
        """
        Update model instance from a Pydantic schema
        
        Args:
            schema: Pydantic schema instance
            exclude_fields: Set of field names to exclude from update
        """
        exclude_fields = exclude_fields or set()
        schema_dict = schema.model_dump(exclude_unset=True)
        
        # Filter out excluded fields and fields that don't exist in the model
        model_fields = {c.key for c in inspect(self.__class__).columns}
        filtered_dict = {
            k: v for k, v in schema_dict.items() 
            if k in model_fields and k not in exclude_fields
        }
        
        for field, value in filtered_dict.items():
            setattr(self, field, value)
    
    def to_schema(self, schema_class: Type[T], include_fields: Optional[set] = None) -> T:
        """
        Convert model instance to a Pydantic schema
        
        Args:
            schema_class: Target Pydantic schema class
            include_fields: Optional set of field names to include (if None, includes all fields)
        """
        model_dict = {}
        for column in inspect(self.__class__).columns:
            if include_fields is None or column.key in include_fields:
                value = getattr(self, column.key)
                model_dict[column.key] = value
        
        return schema_class(**model_dict)
    
    def save(self) -> 'BaseModelMixin':
        """Save the model instance to the database"""
        with transaction():
            db.session.add(self)
        return self
    
    def delete(self) -> None:
        """Delete the model instance from the database"""
        with transaction():
            db.session.delete(self)
    
    @classmethod
    def get_by_id(cls, id: int) -> Optional['BaseModelMixin']:
        """Get model instance by ID"""
        return cls.query.get(id)
    
    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary
        
        Args:
            exclude: Optional set of field names to exclude
        """
        exclude = exclude or set()
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self.__class__).columns
            if c.key not in exclude
        } 