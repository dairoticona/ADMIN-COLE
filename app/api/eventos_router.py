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
    return await crud_evento.create(db, obj_in=evento_in)

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
