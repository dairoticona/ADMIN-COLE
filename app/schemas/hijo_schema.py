from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date

from app.models.hijo_model import GradoEstudiante


class HijoBase(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del hijo")
    apellido: str = Field(..., min_length=1, description="Apellido del hijo")
    curso: GradoEstudiante = Field(..., description="Curso/grado del estudiante")
    fecha_nacimiento: date = Field(..., description="Fecha de nacimiento")
    rude: int = Field(..., description="RUDE del estudiante (16 dígitos)")
    carnet: int = Field(..., description="Número de carnet (8-10 dígitos)")


class HijoCreate(HijoBase):
    """Schema para crear un nuevo hijo (padre_id se auto-rellena)"""
    pass


class HijoUpdate(BaseModel):
    """Schema para actualizar un hijo (todos los campos opcionales)"""
    nombre: Optional[str] = Field(None, min_length=1, description="Nombre del hijo")
    apellido: Optional[str] = Field(None, min_length=1, description="Apellido del hijo")
    curso: Optional[GradoEstudiante] = Field(None, description="Curso/grado del estudiante")
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    rude: Optional[int] = Field(None, description="RUDE del estudiante (16 dígitos)")
    carnet: Optional[int] = Field(None, description="Número de carnet (8-10 dígitos)")


class HijoResponse(HijoBase):
    """Schema para respuesta de hijo"""
    id: str = Field(..., alias="_id")
    padre_id: str = Field(..., description="ID del padre propietario")
    nombre_padre: str = Field(..., description="Nombre del padre")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )
