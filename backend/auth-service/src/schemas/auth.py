from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from shared.schemas.base import BaseSchema
from pydantic.types import SecretStr

class AuthUserBase(BaseSchema):
    email: EmailStr
    is_google_user: bool = False
    first_login: bool = True
    is_email_verified: bool = False
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_picture: Optional[str] = None
    last_login: Optional[datetime] = None

class AuthUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=72)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '@$!%*?&' for c in v):
            raise ValueError('Password must contain at least one special character (@$!%*?&)')
        return v

class AuthUserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_picture: Optional[str] = None

class AuthUserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=72)
    device_info: Optional[Dict[str, Any]] = None

class GoogleLogin(BaseModel):
    token: str
    device_info: Optional[Dict[str, Any]] = None

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12, max_length=72)

    @validator('new_password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '@$!%*?&' for c in v):
            raise ValueError('Password must contain at least one special character (@$!%*?&)')
        return v

class SessionCreate(BaseModel):
    user_id: int
    device_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    expires_at: datetime
    include_refresh_token: bool = True
    refresh_token_expires_at: Optional[datetime] = None

class SessionResponse(BaseModel):
    token: str
    refresh_token: Optional[str] = None
    expires_at: datetime
    refresh_token_expires_at: Optional[datetime] = None
    device_info: Optional[Dict[str, Any]] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None

class TokenRefresh(BaseModel):
    refresh_token: str
    device_info: Optional[Dict[str, Any]] = None

class SessionRevoke(BaseModel):
    session_id: int
    reason: Optional[str] = None

class ActiveSessionsResponse(BaseModel):
    sessions: List[SessionResponse]
    total_count: int

class EmailVerificationCreate(BaseModel):
    user_id: int
    token: str = Field(..., min_length=32)
    expires_at: datetime

class AuthUserResponse(AuthUserBase):
    id: int
    created_at: datetime
    updated_at: datetime 