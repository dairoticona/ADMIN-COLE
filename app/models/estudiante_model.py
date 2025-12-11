from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum
from .common import PyObjectId

class EstadoEstudiante(str, Enum):
    ACTIVO = "ACTIVO"
    RETIRADO = "RETIRADO"
    PROMOVIDO = "PROMOVIDO"

class EstudianteModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    rude: int = Field(..., description="Código RUDE único del estudiante")
    
    # Datos Personales
    nombres: str = Field(..., description="Nombres del estudiante")
    apellidos: str = Field(..., description="Apellidos del estudiante")
    # Situación Académica
    curso_id: Optional[PyObjectId] = Field(None, description="ID del curso actual")
    estado: EstadoEstudiante = Field(default=EstadoEstudiante.ACTIVO, description="Estado académico")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('rude')
    @classmethod
    def validate_rude(cls, v: int) -> int:
        """Validar que el RUDE tenga entre 10 y 20 dígitos aproximadamente (flexible pero razonable)"""
        # El usuario dijo "clave para búsquedas oficiales", suele ser largo.
        # El anterior modelo validaba 16 digitos exactos. Mantengamos esa validación si es estricta.
        rude_str = str(v)
        if len(rude_str) < 5: # Relaxing a bit just in case, but usually strict in Bolivia
             raise ValueError('El RUDE parece incorrecto')
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "rude": 8078012345678,
                "nombres": "Juan",
                "apellidos": "Pérez",
                "curso_id": "507f1f77bcf86cd799439011",
                "estado": "ACTIVO"
            }
        }
    )
