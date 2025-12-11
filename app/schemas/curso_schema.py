from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.curso_model import TurnoCurso, NivelEducativo

from app.models.common import PyObjectId

class CursoBase(BaseModel):
    nombre: str = Field(..., description="Nombre del curso, ej: 'Quinto A'")
    paralelo: str = Field(..., description="Paralelo, ej: 'A', 'B', 'C'")
    nivel: NivelEducativo = Field(..., description="Nivel académico")
    turno: TurnoCurso = Field(..., description="Turno de clases")
    malla_id: PyObjectId = Field(..., description="ID de la Malla Curricular asociada")
    tutor_id: Optional[PyObjectId] = Field(None, description="ID del profesor encargado (Tutor)")

class CursoCreate(CursoBase):
    pass

class CursoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, description="Nombre del curso")
    paralelo: Optional[str] = Field(None, description="Paralelo")
    nivel: Optional[NivelEducativo] = Field(None, description="Nivel académico")
    turno: Optional[TurnoCurso] = Field(None, description="Turno de clases")
    malla_id: Optional[PyObjectId] = Field(None, description="ID de la Malla Curricular")
    tutor_id: Optional[PyObjectId] = Field(None, description="ID del Tutor")

class CursoResponse(CursoBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
