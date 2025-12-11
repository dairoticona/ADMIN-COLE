from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from app.models.licencia_model import EstadoLicencia
from app.models.common import PyObjectId

class LicenciaBase(BaseModel):
    padre_id: PyObjectId = Field(..., description="ID del padre solicitante")
    estudiante_id: PyObjectId = Field(..., description="ID del estudiante que faltará")
    fecha_inicio: date = Field(..., description="Fecha de inicio")
    fecha_fin: date = Field(..., description="Fecha de fin")
    motivo: str = Field(..., description="Motivo de la licencia")
    adjunto: Optional[str] = Field(None, description="URL del adjunto")
    estado: EstadoLicencia = Field(default=EstadoLicencia.PENDIENTE, description="Estado")
    respuesta_admin: Optional[str] = Field(None, description="Respuesta del colegio")

class LicenciaCreate(LicenciaBase):
    pass

class LicenciaUpdate(BaseModel):
    padre_id: Optional[PyObjectId] = Field(None, description="ID del padre")
    estudiante_id: Optional[PyObjectId] = Field(None, description="ID del estudiante")
    fecha_inicio: Optional[date] = Field(None, description="Fecha inicio")
    fecha_fin: Optional[date] = Field(None, description="Fecha fin")
    motivo: Optional[str] = Field(None, description="Motivo")
    adjunto: Optional[str] = Field(None, description="Adjunto")
    estado: Optional[EstadoLicencia] = Field(None, description="Estado")
    respuesta_admin: Optional[str] = Field(None, description="Respuesta admin")

class LicenciaResponse(LicenciaBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )
