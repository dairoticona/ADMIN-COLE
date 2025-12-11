from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.user_model import UserRole
from app.models.common import PyObjectId

# ----------------- Shared/Base -----------------
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    hijos_ids: Optional[List[PyObjectId]] = Field(default=[], description="Lista de IDs de sus hijos")
    is_active: bool = True

class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=6)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    hijos_ids: Optional[List[PyObjectId]] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

# ----------------- Auth / Special -----------------

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    username: str # Usually email
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class UpdateProfileRequest(BaseModel):
    username: str = Field(..., min_length=3)

# Specific Registrations (keeping for compatibility if needed, but updated fields)
class PadreRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Correo electrónico")
    password: str = Field(..., min_length=6, description="Contraseña")
    nombre: str = Field(..., min_length=1, description="Nombre")
    apellido: str = Field(..., min_length=1, description="Apellido")
    # Add other fields as optional or required depending on logic
    telefono: Optional[str] = None
    
class AdminCreateRequest(BaseModel):
    email: EmailStr # Admin username is usually username, but request uses username field logic in router
    username: str = Field(..., min_length=3) # Added username as required by admin_router
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.ADMIN
