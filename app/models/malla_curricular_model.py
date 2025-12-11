from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum
from .common import PyObjectId

class NivelEducativo(str, Enum):
    INICIAL = "INICIAL"
    PRIMARIA = "PRIMARIA"
    SECUNDARIA = "SECUNDARIA"

class AreaEstudio(BaseModel):
    nombre_campo: str = Field(..., description="Nombre del campo, ej: 'Vida Tierra Territorio'")
    materias: List[str] = Field(..., description="Lista de materias, ej: ['Biología', 'Física']")

class MallaCurricularModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    gestion: int = Field(..., description="Año de gestión, ej: 2024")
    nivel: NivelEducativo = Field(..., description="Nivel: Primaria o Secundaria")
    anio_escolaridad: int = Field(..., ge=1, le=6, description="Año de escolaridad (1-6)")
    estructura_areas: List[AreaEstudio] = Field(..., description="Estructura de áreas y materias")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "example": {
                "gestion": 2024,
                "nivel": "SECUNDARIA",
                "anio_escolaridad": 5,
                "estructura_areas": [
                    {
                        "nombre_campo": "Vida Tierra Territorio",
                        "materias": ["Biología", "Geografía", "Física", "Química"]
                    }
                ]
            }
        }
    )
