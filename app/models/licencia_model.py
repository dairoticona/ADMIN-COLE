from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from bson import ObjectId
from enum import Enum
from .common import PyObjectId

class EstadoLicencia(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA" # Changed from ACEPTADA to match schema "Aprobada"
    RECHAZADA = "RECHAZADA"

class TipoPermiso(str, Enum):
    PERSONAL = "PERSONAL"
    MEDICO = "MEDICO"
    FAMILIAR = "FAMILIAR"

class LicenciaModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Solicitante
    padre_id: PyObjectId = Field(..., description="ID del padre solicitante")
    estudiante_id: PyObjectId = Field(..., description="ID del estudiante que faltará")
    
    # Detalle
    tipo_permiso: TipoPermiso = Field(..., description="Tipo de permiso solicitado")
    fecha_inicio: date = Field(..., description="Fecha de inicio de la licencia")
    fecha_fin: date = Field(..., description="Fecha de fin de la licencia")
    motivo: Optional[str] = Field(None, description="Motivo de la licencia (obligatorio para MEDICO y FAMILIAR)")
    adjunto: Optional[str] = Field(None, description="URL del certificado médico u otro adjunto (obligatorio para MEDICO y FAMILIAR)")
    
    # Resolución
    estado: EstadoLicencia = Field(default=EstadoLicencia.PENDIENTE, description="Estado de la solicitud")
    respuesta_admin: Optional[str] = Field(None, description="Respuesta del colegio")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "padre_id": "507f1f77bcf86cd799439011",
                "estudiante_id": "507f1f77bcf86cd799439022",
                "fecha_inicio": "2025-05-20",
                "fecha_fin": "2025-05-22",
                "motivo": "Enfermedad",
                "estado": "PENDIENTE"
            }
        }
    )
