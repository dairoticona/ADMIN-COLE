from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.notificacion_model import TipoNotificacion


class NotificacionCreate(BaseModel):
    """Schema para crear una notificación"""
    type: TipoNotificacion = Field(..., description="Tipo de notificación")
    title: str = Field(..., min_length=1, max_length=200, description="Título de la notificación")
    message: str = Field(..., min_length=1, max_length=1000, description="Mensaje de la notificación")
    related_id: Optional[str] = Field(default=None, description="ID relacionado (ej: licencia_id)")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "license_request",
                "title": "Nueva solicitud de licencia",
                "message": "Un padre ha solicitado una nueva licencia para su hijo",
                "related_id": "507f1f77bcf86cd799439012"
            }
        }


class NotificacionUpdate(BaseModel):
    """Schema para actualizar una notificación"""
    is_read: Optional[bool] = Field(default=None, description="Marcar como leída/no leída")


class NotificacionResponse(BaseModel):
    """Schema de respuesta para notificaciones"""
    id: str = Field(..., alias="_id")
    type: str
    title: str
    message: str
    user_id: str
    is_read: bool
    related_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True
