from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum
from .common import PyObjectId

class EstadoDocumento(str, Enum):
    BORRADOR = "BORRADOR"
    PUBLICADA = "PUBLICADA"

class LibretaModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Metadatos del Estudiante
    estudiante_id: PyObjectId = Field(..., description="ID del estudiante")
    gestion: int = Field(..., description="Ej: 2024")
    
    # Archivo PDF
    titulo: Optional[str] = Field(None, description="Título del documento, ej: Libreta 3er Trimestre")
    archivo_path: str = Field(..., description="Ruta relativa del archivo PDF en el servidor")
    
    # Estado
    estado_documento: EstadoDocumento = Field(default=EstadoDocumento.BORRADOR)

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
