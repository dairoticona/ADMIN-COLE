from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.malla_curricular_model import NivelEducativo, AreaEstudio
from app.models.common import PyObjectId

class MallaCurricularBase(BaseModel):
    gestion: int = Field(..., description="Año de gestión, ej: 2024")
    nivel: NivelEducativo = Field(..., description="Nivel: Primaria o Secundaria")
    anio_escolaridad: int = Field(..., ge=1, le=6, description="Año de escolaridad (1-6)")
    estructura_areas: List[AreaEstudio] = Field(..., description="Estructura de áreas y materias")

class MallaCurricularCreate(MallaCurricularBase):
    pass

class MallaCurricularUpdate(BaseModel):
    gestion: Optional[int] = Field(None, description="Año de gestión")
    nivel: Optional[NivelEducativo] = Field(None, description="Nivel")
    anio_escolaridad: Optional[int] = Field(None, ge=1, le=6, description="Año de escolaridad")
    estructura_areas: Optional[List[AreaEstudio]] = Field(None, description="Estructura de áreas")

class MallaCurricularResponse(MallaCurricularBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
