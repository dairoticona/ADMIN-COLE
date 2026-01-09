from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from app.models.common import PyObjectId
from bson import ObjectId


class TipoNotificacion(str, Enum):
    """Tipos de notificaciones"""
    # Notificaciones para Admins
    LICENSE_REQUEST = "license_request"  # Padre solicita licencia -> Admins
    PAYMENT_SUBMITTED = "payment_submitted"  # Padre registra pago -> Admins
    
    # Notificaciones para Padres
    LICENSE_APPROVED = "license_approved"  # Admin aprueba licencia -> Padre
    LICENSE_REJECTED = "license_rejected"  # Admin rechaza licencia -> Padre
    LICENSE_COMMENTED = "license_commented"  # Admin comenta licencia -> Padre
    EVENT_CREATED = "event_created"  # Admin crea evento/reunión -> Padres
    LIBRETA_PUBLISHED = "libreta_published"  # Admin publica libreta -> Padre
    PAYMENT_APPROVED = "payment_approved"  # Admin aprueba pago -> Padre
    PAYMENT_REJECTED = "payment_rejected"  # Admin rechaza pago -> Padre
    
    # Notificaciones generales
    GENERAL = "general"
    ALERT = "alert"


class NotificacionModel(BaseModel):
    """Modelo de notificación en la base de datos"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    type: TipoNotificacion = Field(..., description="Tipo de notificación")
    title: str = Field(..., description="Título de la notificación")
    message: str = Field(..., description="Mensaje de la notificación")
    user_id: PyObjectId = Field(..., description="ID del usuario destinatario")
    is_read: bool = Field(default=False, description="Estado de lectura")
    related_id: Optional[PyObjectId] = Field(default=None, description="ID relacionado (ej: licencia_id)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "type": "license_request",
                "title": "Nueva solicitud de licencia",
                "message": "Un padre ha solicitado una nueva licencia",
                "user_id": "507f1f77bcf86cd799439011",
                "is_read": False,
                "related_id": "507f1f77bcf86cd799439012"
            }
        }
