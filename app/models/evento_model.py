from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .common import PyObjectId

class EventoModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    titulo: str = Field(..., description="Título del evento")
    descripcion: str = Field(..., description="Descripción detallada")
    fecha_hora: datetime = Field(..., description="Fecha y hora del evento")
    hora_conclusion: Optional[datetime] = Field(None, description="Hora de conclusión del evento")
    
    # Destinatarios
    es_global: bool = Field(False, description="Si es True, visible para todos")
    cursos_permitidos: List[PyObjectId] = Field(default=[], description="Lista de IDs de cursos que pueden ver el evento si no es global")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "titulo": "Reunión de Padres",
                "descripcion": "Entrega de boletines primer trimestre",
                "fecha_hora": "2025-05-10T19:00:00",
                "es_global": False,
                "cursos_permitidos": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
            }
        }
    )
