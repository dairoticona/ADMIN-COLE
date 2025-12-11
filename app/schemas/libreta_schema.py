from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.libreta_model import EstadoLibreta, DatosInstitucionales, ContenidoMateria
from app.models.common import PyObjectId

class LibretaBase(BaseModel):
    estudiante_id: PyObjectId = Field(..., description="ID del estudiante")
    gestion: int = Field(..., description="Ej: 2024")
    datos_institucionales: DatosInstitucionales = Field(..., description="Datos del colegio")
    contenido_academico: List[ContenidoMateria] = Field(..., description="Lista de materias y notas")
    estado_final: EstadoLibreta = Field(default=EstadoLibreta.PENDIENTE)

class LibretaCreate(LibretaBase):
    pass

class LibretaUpdate(BaseModel):
    estudiante_id: Optional[PyObjectId] = Field(None, description="ID del estudiante")
    gestion: Optional[int] = Field(None, description="Gestión")
    datos_institucionales: Optional[DatosInstitucionales] = Field(None, description="Datos institucionales")
    contenido_academico: Optional[List[ContenidoMateria]] = Field(None, description="Contenido académico")
    estado_final: Optional[EstadoLibreta] = Field(None, description="Estado final")

class LibretaResponse(LibretaBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
