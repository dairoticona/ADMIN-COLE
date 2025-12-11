from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from bson import ObjectId
from enum import Enum
from .common import PyObjectId
from .malla_curricular_model import NivelEducativo

class TurnoCurso(str, Enum):
    MANANA = "MAÑANA"
    TARDE = "TARDE"

class CursoModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    nombre: str = Field(..., description="Nombre del curso, ej: 'Quinto A'")
    paralelo: str = Field(..., description="Paralelo, ej: 'A', 'B', 'C'")
    nivel: NivelEducativo = Field(..., description="Nivel académico")
    turno: TurnoCurso = Field(..., description="Turno de clases")
    
    # Configuración Académica
    malla_id: PyObjectId = Field(..., description="ID de la Malla Curricular asociada")
    tutor_id: Optional[PyObjectId] = Field(None, description="ID del profesor encargado (Tutor)")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "example": {
                "nombre": "Quinto A Secundaria",
                "paralelo": "A",
                "nivel": "SECUNDARIA",
                "turno": "MAÑANA",
                "malla_id": "507f1f77bcf86cd799439011",
                "tutor_id": "507f1f77bcf86cd799439012"
            }
        }
    )
