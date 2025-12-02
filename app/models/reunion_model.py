from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime, time
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


class ReunionModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    nombre_reunion: str = Field(..., description="Nombre de la reunión")
    tema: str = Field(..., description="Tema a tratar en la reunión")
    fecha: datetime = Field(..., description="Fecha de la reunión")
    hora_inicio: time = Field(..., description="Hora de inicio de la reunión")
    hora_conclusion: time = Field(..., description="Hora de conclusión de la reunión")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            time: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "nombre_reunion": "Reunión de Planificación",
                "tema": "Planificación del próximo trimestre",
                "fecha": "2025-12-15T00:00:00",
                "hora_inicio": "09:00:00",
                "hora_conclusion": "11:00:00"
            }
        }
    )
