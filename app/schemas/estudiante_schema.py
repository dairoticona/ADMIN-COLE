from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.estudiante_model import EstadoEstudiante
from app.models.common import PyObjectId
from enum import Enum

class GradoFilter(str, Enum):
    PRE_KINDER = "PRE_KINDER"
    KINDER = "KINDER"
    PRIMERO = "PRIMERO"
    SEGUNDO = "SEGUNDO"
    TERCERO = "TERCERO"
    CUARTO = "CUARTO"
    QUINTO = "QUINTO"
    SEXTO = "SEXTO"

class EstudianteBase(BaseModel):
    rude: int = Field(..., description="Código RUDE único del estudiante")
    nombres: str = Field(..., description="Nombres del estudiante")
    apellidos: str = Field(..., description="Apellidos del estudiante")
    curso_id: Optional[PyObjectId] = Field(None, description="ID del curso actual")
    estado: EstadoEstudiante = Field(default=EstadoEstudiante.ACTIVO, description="Estado académico")

class EstudianteCreate(EstudianteBase):
    pass

class EstudianteUpdate(BaseModel):
    rude: Optional[int] = Field(None, description="Código RUDE")
    nombres: Optional[str] = Field(None, description="Nombres")
    apellidos: Optional[str] = Field(None, description="Apellidos")
    curso_id: Optional[PyObjectId] = Field(None, description="ID del curso")
    estado: Optional[EstadoEstudiante] = Field(None, description="Estado académico")

class EstudianteResponse(EstudianteBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
