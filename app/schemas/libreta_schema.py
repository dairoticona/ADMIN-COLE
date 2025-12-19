from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.libreta_model import EstadoDocumento
from app.models.common import PyObjectId

class LibretaBase(BaseModel):
    estudiante_id: PyObjectId = Field(..., description="ID del estudiante")
    gestion: int = Field(..., description="Ej: 2024")
    titulo: Optional[str] = Field(None, description="Título del documento")
    estado_documento: EstadoDocumento = Field(default=EstadoDocumento.BORRADOR)

class LibretaCreate(LibretaBase):
    # En el POST, el archivo se maneja aparte por UploadFile, 
    # pero este schema valida los campos de texto si se usan como JSON (aunque usaremos Form).
    pass

class LibretaUpdate(BaseModel):
    estudiante_id: Optional[PyObjectId] = Field(None)
    gestion: Optional[int] = Field(None)
    titulo: Optional[str] = Field(None)
    estado_documento: Optional[EstadoDocumento] = Field(None)

class LibretaResponse(LibretaBase):
    id: PyObjectId = Field(..., alias="_id")
    archivo_path: str = Field(..., description="Ruta relativa del archivo")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
