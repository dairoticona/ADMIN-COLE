from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


from app.models.user_model import UserRole

class UserBase(BaseModel):
    email: EmailStr
    username: str
    nombre: Optional[str] = ""
    apellido: Optional[str] = ""
    role: Optional[UserRole] = None

class PadreRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, description="Nombre de usuario")
    password: str = Field(..., min_length=6, description="Contraseña")
    email: EmailStr = Field(..., description="Correo electrónico")
    nombre: str = Field(..., min_length=1, description="Nombre del padre")
    apellido: str = Field(..., min_length=1, description="Apellido del padre")

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
