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