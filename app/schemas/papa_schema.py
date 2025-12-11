from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.common import PyObjectId, UserRole

# ----------------- Papa Schemas -----------------
class PapaBase(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = UserRole.PADRE # Default/Fixed
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    hijos_ids: Optional[List[PyObjectId]] = Field(default=[], description="Lista de IDs de sus hijos")
    is_active: bool = True

class PapaCreate(PapaBase):
    email: EmailStr
    password: Optional[str] = Field(None, min_length=6)
    nombre: str
    apellido: str
    # En create, forzamos role PADRE si no viene
    role: UserRole = UserRole.PADRE

class PapaUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    # role: Optional[UserRole] = None # No permitimos cambiar rol en update de papa
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    hijos_ids: Optional[List[PyObjectId]] = None
    is_active: Optional[bool] = None

class PapaResponse(PapaBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
