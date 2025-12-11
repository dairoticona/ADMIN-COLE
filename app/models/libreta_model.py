from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId
from enum import Enum
from .common import PyObjectId

class EstadoLibreta(str, Enum):
    APROBADO = "APROBADO"
    REPROBADO = "REPROBADO"
    PENDIENTE = "PENDIENTE"

class NotasMateria(BaseModel):
    primer_trimestre: float = Field(0, ge=0, le=100)
    segundo_trimestre: float = Field(0, ge=0, le=100)
    tercer_trimestre: float = Field(0, ge=0, le=100)
    promedio_anual: float = Field(0, ge=0, le=100)

class ContenidoMateria(BaseModel):
    materia: str = Field(..., description="Nombre de la materia")
    campo: str = Field(..., description="Nombre del campo")
    notas: NotasMateria = Field(default_factory=NotasMateria)

class DatosInstitucionales(BaseModel):
    nombre_colegio: str
    sie: str
    distrito: str

class LibretaModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Cabecera
    estudiante_id: PyObjectId = Field(..., description="ID del estudiante")
    gestion: int = Field(..., description="Ej: 2024")
    datos_institucionales: DatosInstitucionales = Field(..., description="Copia estática de datos del colegio")
    
    # Contenido Académico
    contenido_academico: List[ContenidoMateria] = Field(..., description="Lista de materias y notas")
    
    estado_final: EstadoLibreta = Field(default=EstadoLibreta.PENDIENTE)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    )
