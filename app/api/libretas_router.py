from typing import List
from fastapi import APIRouter, HTTPException
from app.crud.crud_libreta import libreta as crud_libreta
from app.schemas.libreta_schema import LibretaCreate, LibretaUpdate, LibretaResponse

from app.core.database import get_database

router = APIRouter()

@router.get("/", response_model=List[LibretaResponse])
async def read_libretas(skip: int = 0, limit: int = 100):
    db = get_database()
    return await crud_libreta.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=LibretaResponse)
async def create_libreta(libreta_in: LibretaCreate):
    db = get_database()
    return await crud_libreta.create(db, obj_in=libreta_in)

@router.get("/{id}", response_model=LibretaResponse)
async def read_libreta(id: str):
    db = get_database()
    libreta = await crud_libreta.get(db, id=id)
    if not libreta:
        raise HTTPException(status_code=404, detail="Libreta not found")
    return libreta

@router.put("/{id}", response_model=LibretaResponse)
async def update_libreta(id: str, libreta_in: LibretaUpdate):
    db = get_database()
    libreta = await crud_libreta.get(db, id=id)
    if not libreta:
        raise HTTPException(status_code=404, detail="Libreta not found")
    return await crud_libreta.update(db, db_obj=libreta, obj_in=libreta_in)

@router.delete("/{id}", response_model=LibretaResponse)
async def delete_libreta(id: str):
    db = get_database()
    libreta = await crud_libreta.get(db, id=id)
    if not libreta:
        raise HTTPException(status_code=404, detail="Libreta not found")
    return await crud_libreta.remove(db, id=id)
