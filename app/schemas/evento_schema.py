from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.common import PyObjectId

class EventoBase(BaseModel):
    titulo: str = Field(..., description="Título del evento")
    descripcion: str = Field(..., description="Descripción detallada")
    fecha_hora: datetime = Field(..., description="Fecha y hora del evento")
    hora_conclusion: Optional[datetime] = Field(None, description="Hora de conclusión del evento")
    es_global: bool = Field(False, description="Si es True, visible para todos")
    cursos_permitidos: List[PyObjectId] = Field(default=[], description="Lista de IDs de cursos")

class EventoCreate(EventoBase):
    pass

class EventoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, description="Título del evento")
    descripcion: Optional[str] = Field(None, description="Descripción")
    fecha_hora: Optional[datetime] = Field(None, description="Fecha y hora")
    hora_conclusion: Optional[datetime] = Field(None, description="Hora de conclusión")
    es_global: Optional[bool] = Field(None, description="Visibilidad global")
    cursos_permitidos: Optional[List[PyObjectId]] = Field(None, description="Cursos permitidos")

class EventoResponse(EventoBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
