from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, time


class ReunionBase(BaseModel):
    nombre_reunion: str = Field(..., min_length=1, description="Nombre de la reunión")
    tema: str = Field(..., min_length=1, description="Tema a tratar en la reunión")
    fecha: datetime = Field(..., description="Fecha de la reunión")
    hora_inicio: time = Field(..., description="Hora de inicio de la reunión")
    hora_conclusion: time = Field(..., description="Hora de conclusión de la reunión")


class ReunionCreate(ReunionBase):
    """Schema para crear una nueva reunión"""
    pass


class ReunionUpdate(BaseModel):
    """Schema para actualizar una reunión (todos los campos son opcionales)"""
    nombre_reunion: Optional[str] = Field(None, min_length=1, description="Nombre de la reunión")
    tema: Optional[str] = Field(None, min_length=1, description="Tema a tratar en la reunión")
    fecha: Optional[datetime] = Field(None, description="Fecha de la reunión")
    hora_inicio: Optional[time] = Field(None, description="Hora de inicio de la reunión")
    hora_conclusion: Optional[time] = Field(None, description="Hora de conclusión de la reunión")


class ReunionResponse(ReunionBase):
    """Schema para respuesta de reunión"""
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            time: lambda v: v.isoformat()
        }
    )
