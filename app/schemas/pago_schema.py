from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from app.models.pago_model import EstadoPago, ComprobantePago
from app.models.common import PyObjectId

class PagoBase(BaseModel):
    padre_id: PyObjectId = Field(..., description="Usuario (Padre) que realiza el pago")
    estudiante_id: PyObjectId = Field(..., description="Estudiante asociado")
    concepto: str = Field(..., description="Ej: 'Mensualidad Mayo'")
    monto: float = Field(..., description="Monto a pagar")
    fecha_vencimiento: date = Field(..., description="Fecha límite de pago")
    estado: EstadoPago = Field(default=EstadoPago.PENDIENTE, description="Estado del pago")
    comprobante: Optional[ComprobantePago] = Field(None, description="Detalles del comprobante")

class PagoCreate(PagoBase):
    pass

class PagoUpdate(BaseModel):
    padre_id: Optional[PyObjectId] = Field(None, description="Padre ID")
    estudiante_id: Optional[PyObjectId] = Field(None, description="Estudiante ID")
    concepto: Optional[str] = Field(None, description="Concepto")
    monto: Optional[float] = Field(None, description="Monto")
    fecha_vencimiento: Optional[date] = Field(None, description="Fecha vencimiento")
    estado: Optional[EstadoPago] = Field(None, description="Estado")
    comprobante: Optional[ComprobantePago] = Field(None, description="Comprobante")

class PagoResponse(PagoBase):
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
