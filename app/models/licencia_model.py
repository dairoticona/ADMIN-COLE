from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime, date
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from enum import Enum

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: Any
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


class TipoPermiso(str, Enum):
    MEDICO = "MEDICO"
    PERSONAL = "PERSONAL"
    FAMILIAR = "FAMILIAR"
    OTROS = "OTROS"


class GradoEstudiante(str, Enum):
    KINDER = "KINDER"
    PRIMERO_PRIMARIA = "1RO_PRIMARIA"
    SEGUNDO_PRIMARIA = "2DO_PRIMARIA"
    TERCERO_PRIMARIA = "3RO_PRIMARIA"
    CUARTO_PRIMARIA = "4TO_PRIMARIA"
    QUINTO_PRIMARIA = "5TO_PRIMARIA"
    SEXTO_PRIMARIA = "6TO_PRIMARIA"
    PRIMERO_SECUNDARIA = "1RO_SECUNDARIA"
    SEGUNDO_SECUNDARIA = "2DO_SECUNDARIA"
    TERCERO_SECUNDARIA = "3RO_SECUNDARIA"
    CUARTO_SECUNDARIA = "4TO_SECUNDARIA"
    QUINTO_SECUNDARIA = "5TO_SECUNDARIA"
    SEXTO_SECUNDARIA = "6TO_SECUNDARIA"


class EstadoLicencia(str, Enum):
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"


class LicenciaModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    nombre_estudiante: str = Field(..., description="Nombre del estudiante")
    nombre_padre: str = Field(..., description="Nombre del padre (auto-rellenado)")
    tipo_permiso: TipoPermiso = Field(..., description="Tipo de permiso")
    grado_estudiante: GradoEstudiante = Field(..., description="Grado del estudiante")
    fecha: date = Field(..., description="Fecha del permiso")
    cantidad_dias: int = Field(..., ge=1, description="Cantidad de días del permiso")
    motivo: str = Field(..., min_length=1, description="Motivo del permiso")
    estado: EstadoLicencia = Field(default=EstadoLicencia.PENDIENTE, description="Estado de la licencia")
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
                "nombre_estudiante": "Juan Pérez",
                "nombre_padre": "Carlos Pérez",
                "tipo_permiso": "MEDICO",
                "grado_estudiante": "3RO_PRIMARIA",
                "fecha": "2025-12-15",
                "cantidad_dias": 2,
                "motivo": "Cita médica programada",
                "estado": "PENDIENTE"
            }
        }
    )
