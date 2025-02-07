from datetime import datetime
from typing import Optional, Any, Literal
from pydantic import BaseModel, Field
from .base import BaseSchema

class AuditLogBase(BaseSchema):
    meeting_id: int
    user_id: Optional[int] = None
    action: Literal[
        'meeting_created',
        'meeting_updated',
        'meeting_started',
        'meeting_ended',
        'participant_joined',
        'participant_left',
        'participant_approved',
        'participant_declined',
        'participant_banned',
        'co_host_added',
        'co_host_removed',
        'recording_started',
        'recording_stopped',
        'chat_disabled',
        'chat_enabled',
        'screen_share_started',
        'screen_share_stopped'
    ]
    details: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=45)

class AuditLogCreate(BaseModel):
    meeting_id: int
    user_id: Optional[int] = None
    action: Literal[
        'meeting_created',
        'meeting_updated',
        'meeting_started',
        'meeting_ended',
        'participant_joined',
        'participant_left',
        'participant_approved',
        'participant_declined',
        'participant_banned',
        'co_host_added',
        'co_host_removed',
        'recording_started',
        'recording_stopped',
        'chat_disabled',
        'chat_enabled',
        'screen_share_started',
        'screen_share_stopped'
    ]
    details: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=45)

class AuditLogResponse(AuditLogBase):
    user_name: Optional[str] = None
    meeting_title: Optional[str] = None 