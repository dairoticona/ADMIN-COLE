from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional
from datetime import datetime, date
from app.models.licencia_model import EstadoLicencia, TipoPermiso
from app.models.common import PyObjectId

class LicenciaBase(BaseModel):
    estudiante_id: PyObjectId = Field(..., description="ID del estudiante que faltará")
    tipo_permiso: TipoPermiso = Field(..., description="Tipo de permiso")
    fecha_inicio: date = Field(..., description="Fecha de inicio")
    fecha_fin: date = Field(..., description="Fecha de fin")
    motivo: Optional[str] = Field(None, description="Motivo de la licencia")
    adjunto: Optional[str] = Field(None, description="URL del adjunto")

class LicenciaCreate(LicenciaBase):
    padre_id: Optional[PyObjectId] = Field(None, description="ID del padre (obligatorio si es admin)")
    
    @model_validator(mode='after')
    def validate_tipo_permiso_requirements(self):
        """Validar que MEDICO y FAMILIAR tengan motivo y adjunto"""
        if self.tipo_permiso in [TipoPermiso.MEDICO, TipoPermiso.FAMILIAR]:
            if not self.motivo:
                raise ValueError(f"El motivo es obligatorio para licencias de tipo {self.tipo_permiso.value}")
            if not self.adjunto:
                raise ValueError(f"El adjunto es obligatorio para licencias de tipo {self.tipo_permiso.value}")
        return self

class LicenciaUpdate(BaseModel):
    # padre_id no debería ser actualizable
    estudiante_id: Optional[PyObjectId] = Field(None, description="ID del estudiante")
    tipo_permiso: Optional[TipoPermiso] = Field(None, description="Tipo de permiso")
    fecha_inicio: Optional[date] = Field(None, description="Fecha inicio")
    fecha_fin: Optional[date] = Field(None, description="Fecha fin")
    motivo: Optional[str] = Field(None, description="Motivo")
    adjunto: Optional[str] = Field(None, description="Adjunto")
    # Estado y Respuesta (Opcionales para que Admin pueda actualizarlos)
    estado: Optional[EstadoLicencia] = Field(None, description="Estado (Solo Admin)")
    respuesta_admin: Optional[str] = Field(None, description="Respuesta del colegio (Solo Admin)")

class LicenciaResponse(LicenciaBase):
    id: PyObjectId = Field(..., alias="_id")
    padre_id: PyObjectId = Field(..., description="ID del padre solicitante")
    estado: EstadoLicencia = Field(default=EstadoLicencia.PENDIENTE, description="Estado")
    respuesta_admin: Optional[str] = Field(None, description="Respuesta del colegio")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )

