from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId

from app.core.database import get_database
from app.models.common import UserRole
from app.models.notificacion_model import TipoNotificacion
from app.schemas.notificacion_schema import (
    NotificacionCreate,
    NotificacionUpdate,
    NotificacionResponse
)
from app.crud.crud_notificacion import notificacion as crud_notificacion
from app.api.auth_router import get_current_user

router = APIRouter()


@router.post("/", response_model=List[NotificacionResponse], status_code=status.HTTP_201_CREATED)
async def create_notificacion(
    notificacion_data: NotificacionCreate,
    padre_id: Optional[str] = None,  # Para notificaciones a un padre específico
    current_user: dict = Depends(get_current_user)
):
    """
    Crear una notificación.
    
    **Notificaciones para TODOS los ADMINS:**
    - `license_request`: Cuando un padre solicita una licencia
    - `payment_submitted`: Cuando un padre registra un pago
    
    **Notificaciones para un PADRE específico:**
    - `license_approved`: Cuando se aprueba una licencia (requiere padre_id)
    - `license_rejected`: Cuando se rechaza una licencia (requiere padre_id)
    - `license_commented`: Cuando se comenta una licencia (requiere padre_id)
    - `libreta_published`: Cuando se publica una libreta (requiere padre_id)
    - `payment_approved`: Cuando se aprueba un pago (requiere padre_id)
    - `payment_rejected`: Cuando se rechaza un pago (requiere padre_id)
    
    **Notificaciones para TODOS los PADRES:**
    - `event_created`: Cuando se crea un evento/reunión
    
    **Parámetros:**
    - `padre_id`: ID del padre destinatario (requerido para notificaciones individuales)
    """
    db = get_database()
    
    # Convertir el schema a dict
    notif_dict = notificacion_data.model_dump()
    
    # Convertir related_id a ObjectId si existe
    if notif_dict.get("related_id"):
        if not ObjectId.is_valid(notif_dict["related_id"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID relacionado inválido"
            )
        notif_dict["related_id"] = ObjectId(notif_dict["related_id"])
    
    # Convertir enum a string
    if hasattr(notif_dict.get("type"), "value"):
        notif_dict["type"] = notif_dict["type"].value
    
    created_notifications = []
    
    # === NOTIFICACIONES PARA TODOS LOS ADMINS ===
    if notificacion_data.type in [TipoNotificacion.LICENSE_REQUEST, TipoNotificacion.PAYMENT_SUBMITTED]:
        # Obtener todos los usuarios con rol ADMIN
        users_collection = db["users"]
        admin_users = []
        
        cursor = users_collection.find({"role": UserRole.ADMIN, "is_active": True})
        async for admin in cursor:
            admin_users.append(admin)
        
        if not admin_users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron administradores activos"
            )
        
        # Crear una notificación para cada administrador
        notifications_to_create = []
        for admin in admin_users:
            notif_copy = notif_dict.copy()
            notif_copy["user_id"] = admin["_id"]
            notifications_to_create.append(notif_copy)
        
        # Crear todas las notificaciones en batch
        created_notifications = await crud_notificacion.create_many(db, notifications_to_create)
    
    # === NOTIFICACIONES PARA UN PADRE ESPECÍFICO ===
    elif notificacion_data.type in [
        TipoNotificacion.LICENSE_APPROVED,
        TipoNotificacion.LICENSE_REJECTED,
        TipoNotificacion.LICENSE_COMMENTED,
        TipoNotificacion.LIBRETA_PUBLISHED,
        TipoNotificacion.PAYMENT_APPROVED,
        TipoNotificacion.PAYMENT_REJECTED
    ]:
        # Validar que se proporcionó padre_id
        if not padre_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El tipo de notificación '{notificacion_data.type}' requiere especificar 'padre_id'"
            )
        
        if not ObjectId.is_valid(padre_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de padre inválido"
            )
        
        # Verificar que el padre existe
        users_collection = db["users"]
        padre = await users_collection.find_one({
            "_id": ObjectId(padre_id),
            "role": UserRole.PADRE
        })
        
        if not padre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Padre no encontrado"
            )
        
        # Crear notificación para el padre
        notif_dict["user_id"] = ObjectId(padre_id)
        created_notification = await crud_notificacion.create(db, notif_dict)
        created_notifications = [created_notification]
    
    # === NOTIFICACIONES PARA TODOS LOS PADRES ===
    elif notificacion_data.type == TipoNotificacion.EVENT_CREATED:
        # Obtener todos los usuarios con rol PADRE
        users_collection = db["users"]
        padre_users = []
        
        cursor = users_collection.find({"role": UserRole.PADRE, "is_active": True})
        async for padre in cursor:
            padre_users.append(padre)
        
        if not padre_users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron padres activos"
            )
        
        # Crear una notificación para cada padre
        notifications_to_create = []
        for padre in padre_users:
            notif_copy = notif_dict.copy()
            notif_copy["user_id"] = padre["_id"]
            notifications_to_create.append(notif_copy)
        
        # Crear todas las notificaciones en batch
        created_notifications = await crud_notificacion.create_many(db, notifications_to_create)
    
    # === NOTIFICACIONES GENERALES ===
    else:
        # Para otros tipos de notificaciones, asignar al usuario actual
        notif_dict["user_id"] = ObjectId(current_user["_id"])
        created_notification = await crud_notificacion.create(db, notif_dict)
        created_notifications = [created_notification]
    
    # Convertir ObjectIds a strings para la respuesta
    response_notifications = []
    for notif in created_notifications:
        notif["_id"] = str(notif["_id"])
        notif["user_id"] = str(notif["user_id"])
        if notif.get("related_id"):
            notif["related_id"] = str(notif["related_id"])
        response_notifications.append(notif)
    
    return response_notifications



@router.get("/", response_model=List[NotificacionResponse])
async def list_notificaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_read: Optional[bool] = Query(None, description="Filtrar por estado de lectura"),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar notificaciones del usuario actual.
    
    - Los usuarios solo ven sus propias notificaciones
    - Se pueden filtrar por estado de lectura
    """
    db = get_database()
    
    notifications = await crud_notificacion.get_by_user(
        db,
        user_id=current_user["_id"],
        skip=skip,
        limit=limit,
        is_read=is_read
    )
    
    return notifications


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener el número de notificaciones no leídas del usuario actual.
    """
    db = get_database()
    
    count = await crud_notificacion.count_unread(db, current_user["_id"])
    
    return {"unread_count": count}


@router.get("/{notificacion_id}", response_model=NotificacionResponse)
async def get_notificacion(
    notificacion_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener una notificación específica por ID.
    """
    if not ObjectId.is_valid(notificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de notificación inválido"
        )
    
    db = get_database()
    
    notificacion = await crud_notificacion.get_by_id(db, notificacion_id)
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    # Verificar que la notificación pertenece al usuario actual
    if str(notificacion["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver esta notificación"
        )
    
    return notificacion


@router.patch("/{notificacion_id}/read", response_model=NotificacionResponse)
async def mark_notificacion_as_read(
    notificacion_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Marcar una notificación como leída.
    """
    if not ObjectId.is_valid(notificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de notificación inválido"
        )
    
    db = get_database()
    
    # Verificar que la notificación existe y pertenece al usuario
    notificacion = await crud_notificacion.get_by_id(db, notificacion_id)
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    if str(notificacion["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para modificar esta notificación"
        )
    
    # Marcar como leída
    await crud_notificacion.mark_as_read(db, notificacion_id)
    
    # Obtener la notificación actualizada
    updated_notificacion = await crud_notificacion.get_by_id(db, notificacion_id)
    
    return updated_notificacion


@router.patch("/mark-all-read", response_model=dict)
async def mark_all_as_read(
    current_user: dict = Depends(get_current_user)
):
    """
    Marcar todas las notificaciones del usuario como leídas.
    """
    db = get_database()
    
    count = await crud_notificacion.mark_all_as_read(db, current_user["_id"])
    
    return {
        "message": f"{count} notificaciones marcadas como leídas",
        "count": count
    }


@router.delete("/{notificacion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notificacion(
    notificacion_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Eliminar una notificación.
    """
    if not ObjectId.is_valid(notificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de notificación inválido"
        )
    
    db = get_database()
    
    # Verificar que la notificación existe y pertenece al usuario
    notificacion = await crud_notificacion.get_by_id(db, notificacion_id)
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    if str(notificacion["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar esta notificación"
        )
    
    # Eliminar la notificación
    await crud_notificacion.delete(db, notificacion_id)
    
    return None
