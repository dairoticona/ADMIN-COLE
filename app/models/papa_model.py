from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum
from .common import PyObjectId, UserRole

# Reusing UserRole or defining distinct? 
# If Auth expects UserRole, we should keep compatibility or import it.
# We'll import UserRole from common for compatibility.

# PapaModel mimics UserModel but might be specific for Papas.
# But for now, identical structure to map to 'users' collection correctly.
class PapaModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Credenciales
    email: EmailStr = Field(..., description="Correo electrónico (login)")
    hashed_password: str = Field(..., description="Contraseña encriptada")
    role: UserRole = Field(default=UserRole.PADRE, description="Rol del usuario (Siempre PADRE)")
    
    # Datos Personales
    nombre: str = Field(..., description="Nombres")
    apellido: str = Field(..., description="Apellidos")

    telefono: Optional[str] = Field(None, description="Teléfono o celular")
    direccion: Optional[str] = Field(None, description="Domicilio")
    
    # Referencias (Papas tienen hijos)
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
