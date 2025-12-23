from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum
from .common import PyObjectId

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    PADRE = "PADRE"
    SECRETARIA = "SECRETARIA"

class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Credenciales
    email: EmailStr = Field(..., description="Correo electrónico (login)")
    hashed_password: str = Field(..., description="Contraseña encriptada")
    role: UserRole = Field(..., description="Rol del usuario")
    
    # Datos Personales
    nombre: str = Field(..., description="Nombres") # Mantengo separado para flexibilidad aunque schema diga Completo
    apellido: str = Field(..., description="Apellidos")
    username: Optional[str] = Field(None, description="Nombre de usuario (para administradores)")

    telefono: Optional[str] = Field(None, description="Teléfono o celular")
    direccion: Optional[str] = Field(None, description="Domicilio")
    
    # Referencias (Solo para Padres)
    hijos_ids: List[PyObjectId] = Field(default=[], description="Lista de IDs de sus hijos (Estudiantes)")

    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "example": {
                "email": "padre@example.com",
                "role": "PADRE",
                "nombre": "Juan",
                "apellido": "Pérez",
                "telefono": "77712345",
                "hijos_ids": ["507f1f77bcf86cd799439011"]
            }
        }
    )
