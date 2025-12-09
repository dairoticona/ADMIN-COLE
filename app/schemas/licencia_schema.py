from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date

from app.models.licencia_model import TipoPermiso, GradoEstudiante, EstadoLicencia


class LicenciaBase(BaseModel):
    tipo_permiso: TipoPermiso = Field(..., description="Tipo de permiso")
    fecha: date = Field(..., description="Fecha del permiso")
    cantidad_dias: int = Field(..., ge=1, description="Cantidad de días del permiso")
    motivo: str = Field(..., min_length=1, description="Motivo del permiso")


class LicenciaCreate(LicenciaBase):
    """Schema para crear una nueva licencia (datos del estudiante y padre se auto-rellenan desde el hijo)"""
    hijo_id: str = Field(..., description="ID del hijo registrado")


class LicenciaUpdate(BaseModel):
    """Schema para actualizar una licencia (todos los campos son opcionales, hijo_id no se puede cambiar)"""
    tipo_permiso: Optional[TipoPermiso] = Field(None, description="Tipo de permiso")
    fecha: Optional[date] = Field(None, description="Fecha del permiso")
    cantidad_dias: Optional[int] = Field(None, ge=1, description="Cantidad de días del permiso")
    motivo: Optional[str] = Field(None, min_length=1, description="Motivo del permiso")


class LicenciaResponse(BaseModel):
    """Schema para respuesta de licencia"""
    id: str = Field(..., alias="_id")
    hijo_id: str = Field(..., description="ID del hijo registrado")
    nombre_estudiante: str = Field(..., description="Nombre del estudiante")
    nombre_padre: str = Field(..., description="Nombre del padre")
    tipo_permiso: TipoPermiso = Field(..., description="Tipo de permiso")
    grado_estudiante: GradoEstudiante = Field(..., description="Grado del estudiante")
    fecha: date = Field(..., description="Fecha del permiso")
    cantidad_dias: int = Field(..., ge=1, description="Cantidad de días del permiso")
    motivo: str = Field(..., min_length=1, description="Motivo del permiso")
    estado: EstadoLicencia = Field(..., description="Estado de la licencia")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )
