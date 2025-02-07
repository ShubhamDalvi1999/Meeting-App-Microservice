from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from .base import BaseSchema

class CoHostBase(BaseSchema):
    meeting_id: int
    user_id: int
    can_manage_participants: bool = True
    can_edit_meeting: bool = False
    can_end_meeting: bool = False

class CoHostCreate(BaseModel):
    meeting_id: int
    user_id: int
    can_manage_participants: bool = True
    can_edit_meeting: bool = False
    can_end_meeting: bool = False

class CoHostUpdate(BaseModel):
    can_manage_participants: Optional[bool] = None
    can_edit_meeting: Optional[bool] = None
    can_end_meeting: Optional[bool] = None

class CoHostResponse(CoHostBase):
    user_name: Optional[str] = None
    user_email: Optional[str] = None

class CoHostBulkCreate(BaseModel):
    meeting_id: int
    co_hosts: List[int]  # List of user IDs
    can_manage_participants: bool = True
    can_edit_meeting: bool = False
    can_end_meeting: bool = False 