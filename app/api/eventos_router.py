from typing import List
from fastapi import APIRouter, HTTPException
from app.crud.crud_evento import evento as crud_evento
from app.schemas.evento_schema import EventoCreate, EventoUpdate, EventoResponse

from app.core.database import get_database

router = APIRouter()

@router.get("/", response_model=List[EventoResponse])
async def read_eventos(skip: int = 0, limit: int = 100):
    db = get_database()
    return await crud_evento.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=EventoResponse)
async def create_evento(evento_in: EventoCreate):
    db = get_database()
    evento = await crud_evento.create(db, obj_in=evento_in)
    
    # === ENVIAR NOTIFICACIÓN A TODOS LOS PADRES ===
    from app.crud.crud_notificacion import notificacion as crud_notificacion
    from app.models.common import UserRole
    from bson import ObjectId
    
    try:
        # Obtener todos los padres activos
        users_collection = db["users"]
        padre_users = []
        
        cursor = users_collection.find({"role": UserRole.PADRE, "is_active": True})
        async for padre in cursor:
            padre_users.append(padre)
        
        if padre_users:
            # Crear notificaciones para todos los padres
            notifications_to_create = []
            for padre in padre_users:
                notif_data = {
                    "type": "event_created",
                    "title": f"Nuevo Evento: {evento.get('titulo', 'Sin título')}",
                    "message": f"Se ha programado un nuevo evento. Fecha: {evento.get('fecha', 'Por confirmar')}",
                    "user_id": padre["_id"],
                    "related_id": ObjectId(evento["_id"]) if isinstance(evento.get("_id"), str) else evento.get("_id")
                }
                notifications_to_create.append(notif_data)
            
            await crud_notificacion.create_many(db, notifications_to_create)
    except Exception as e:
        # No fallar si las notificaciones fallan, solo registrar
        print(f"Error al crear notificaciones de evento: {e}")
    
    return evento


@router.get("/{id}", response_model=EventoResponse)
async def read_evento(id: str):
    db = get_database()
    evento = await crud_evento.get(db, id=id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento not found")
    return evento

@router.put("/{id}", response_model=EventoResponse)
async def update_evento(id: str, evento_in: EventoUpdate):
    db = get_database()
    evento = await crud_evento.get(db, id=id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento not found")
    return await crud_evento.update(db, db_obj=evento, obj_in=evento_in)

@router.delete("/{id}", response_model=EventoResponse)
async def delete_evento(id: str):
    db = get_database()
    evento = await crud_evento.get(db, id=id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento not found")
    return await crud_evento.remove(db, id=id)
