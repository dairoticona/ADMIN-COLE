from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from bson import ObjectId
from enum import Enum
from .common import PyObjectId

class EstadoPago(str, Enum):
    PENDIENTE = "PENDIENTE"
    REVISION = "REVISION"
    PAGADO = "PAGADO"
    RECHAZADO = "RECHAZADO"

class ComprobantePago(BaseModel):
    url_foto: str = Field(..., description="URL de la imagen del comprobante")
    fecha_subida: datetime = Field(default_factory=datetime.utcnow)
    fecha_resolucion: Optional[datetime] = Field(None, description="Fecha de aprobación o rechazo")

class PagoModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Relaciones
    padre_id: PyObjectId = Field(..., description="Usuario (Padre) que realiza el pago")
    estudiante_id: PyObjectId = Field(..., description="Estudiante asociado a la mensualidad")

    # Detalle Económico
    concepto: str = Field(..., description="Ej: 'Mensualidad Mayo'")
    monto: float = Field(..., description="Monto a pagar")
    fecha_vencimiento: date = Field(..., description="Fecha límite de pago")

    # Proceso de Validación
    estado: EstadoPago = Field(default=EstadoPago.PENDIENTE, description="Estado del pago")
    comprobante: Optional[ComprobantePago] = Field(None, description="Detalles del comprobante si existe")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )
