from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.schemas.auth_schemas import UserRole

class AdminCreateRequest(BaseModel):
    username: str
    password: str = Field(..., min_length=6)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class UpdateProfileRequest(BaseModel):
    username: str
