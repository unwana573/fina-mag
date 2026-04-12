from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    currency: str
    two_fa_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    currency: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str