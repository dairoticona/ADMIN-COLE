from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Any
from datetime import datetime, date
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

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


from enum import Enum

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


class HijoModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    nombre: str = Field(..., min_length=1, description="Nombre del hijo")
    apellido: str = Field(..., min_length=1, description="Apellido del hijo")
    curso: GradoEstudiante = Field(..., description="Curso/grado del estudiante")
    fecha_nacimiento: date = Field(..., description="Fecha de nacimiento")
    rude: int = Field(..., description="RUDE del estudiante (16 dígitos)")
    carnet: int = Field(..., description="Número de carnet (8-10 dígitos)")
    padre_id: str = Field(..., description="ID del padre propietario")
    nombre_padre: str = Field(..., description="Nombre del padre (para referencia)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('rude')
    @classmethod
    def validate_rude(cls, v: int) -> int:
        """Validar que el RUDE tenga exactamente 16 dígitos"""
        rude_str = str(v)
        if len(rude_str) != 16:
            raise ValueError('El RUDE debe tener exactamente 16 dígitos')
        return v

    @field_validator('carnet')
    @classmethod
    def validate_carnet(cls, v: int) -> int:
        """Validar que el carnet tenga entre 8 y 10 dígitos"""
        carnet_str = str(v)
        if len(carnet_str) < 8 or len(carnet_str) > 10:
            raise ValueError('El carnet debe tener entre 8 y 10 dígitos')
        return v

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
                "nombre": "Carlos",
                "apellido": "López",
                "curso": "3RO_PRIMARIA",
                "fecha_nacimiento": "2015-05-20",
                "rude": 1234567890123456,
                "carnet": 12345678,
                "padre_id": "507f1f77bcf86cd799439011",
                "nombre_padre": "Juan López"
            }
        }
    )
