from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, validator
from .base import BaseSchema

class MeetingBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    meeting_type: Literal['regular', 'recurring', 'private'] = 'regular'
    max_participants: Optional[int] = Field(None, gt=0)
    requires_approval: bool = False
    is_recorded: bool = False
    recording_url: Optional[str] = None
    recurring_pattern: Optional[Literal['daily', 'weekly', 'monthly', 'custom']] = None
    parent_meeting_id: Optional[int] = None
    ended_at: Optional[datetime] = None

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    meeting_type: Literal['regular', 'recurring', 'private'] = 'regular'
    max_participants: Optional[int] = Field(None, gt=0)
    requires_approval: bool = False
    is_recorded: bool = False
    recurring_pattern: Optional[Literal['daily', 'weekly', 'monthly', 'custom']] = None
    parent_meeting_id: Optional[int] = None

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_participants: Optional[int] = Field(None, gt=0)
    requires_approval: Optional[bool] = None
    is_recorded: Optional[bool] = None
    recording_url: Optional[str] = None

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class MeetingResponse(MeetingBase):
    id: int
    created_by: int
    participant_count: Optional[int] = None
    co_hosts: Optional[List[int]] = None 