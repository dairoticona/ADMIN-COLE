from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


from app.models.user_model import UserRole

class UserBase(BaseModel):
    email: EmailStr
    username: str
    nombre: str
    apellido: str
    role: UserRole

class PadreRegisterRequest(BaseModel):
    email: EmailStr
    username: str
    nombre: str
    apellido: str
    password: str = Field(..., min_length=6)

class AdminCreateRequest(BaseModel):
    username: str
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: str = Field(..., alias="_id")
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(
        populate_by_name=True
    )

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class UpdateProfileRequest(BaseModel):
    username: str
