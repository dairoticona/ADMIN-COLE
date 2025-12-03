from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class PadreBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class PadreCreate(PadreBase):
    """Schema para crear un nuevo padre"""
    password: str = Field(..., min_length=6)


class PadreUpdate(BaseModel):
    """Schema para actualizar un padre (todos los campos son opcionales)"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


class PadreResponse(PadreBase):
    """Schema para respuesta de padre"""
    id: str = Field(..., alias="_id")
    is_active: bool

    model_config = ConfigDict(
        populate_by_name=True
    )


class PadreToken(BaseModel):
    """Token de acceso para padres"""
    access_token: str
    token_type: str


class PadreLoginRequest(BaseModel):
    """Request para login de padres"""
    email: EmailStr
    password: str
