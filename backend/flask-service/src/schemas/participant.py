from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator, confloat
from .base import BaseSchema

class ParticipantBase(BaseSchema):
    meeting_id: int
    user_id: int
    status: Literal['pending', 'approved', 'declined', 'banned'] = 'pending'
    role: Literal['attendee', 'presenter', 'moderator'] = 'attendee'
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    is_banned: bool = False
    total_time: Optional[int] = Field(None, ge=0)  # in seconds
    connection_quality: Optional[confloat(ge=0, le=1)] = None
    participation_score: Optional[confloat(ge=0, le=1)] = None
    feedback: Optional[str] = None

class ParticipantCreate(BaseModel):
    meeting_id: int
    user_id: int
    status: Literal['pending', 'approved', 'declined', 'banned'] = 'pending'
    role: Literal['attendee', 'presenter', 'moderator'] = 'attendee'

class ParticipantUpdate(BaseModel):
    status: Optional[Literal['pending', 'approved', 'declined', 'banned']] = None
    role: Optional[Literal['attendee', 'presenter', 'moderator']] = None
    is_banned: Optional[bool] = None
    feedback: Optional[str] = None

class ParticipantJoin(BaseModel):
    meeting_id: int
    user_id: int
    connection_quality: Optional[confloat(ge=0, le=1)] = None

    @validator('connection_quality')
    def validate_connection_quality(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Connection quality must be between 0 and 1')
        return v

class ParticipantLeave(BaseModel):
    meeting_id: int
    user_id: int
    total_time: int = Field(..., ge=0)
    participation_score: confloat(ge=0, le=1)
    feedback: Optional[str] = None

class ParticipantResponse(ParticipantBase):
    user_name: Optional[str] = None
    user_email: Optional[str] = None 