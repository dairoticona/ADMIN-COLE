from typing import List, Optional
import math
from fastapi import APIRouter, HTTPException, Query
from app.crud.crud_libreta import libreta as crud_libreta
from app.schemas.libreta_schema import LibretaCreate, LibretaUpdate, LibretaResponse
from app.schemas.common import PaginatedResponse
from app.core.database import get_database

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[LibretaResponse])
async def read_libretas(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    q: Optional[str] = None
):
    db = get_database()
    items, total = await crud_libreta.get_paginated(db, page=page, per_page=per_page, q=q)
    
    # Calcular total de páginas
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": items
    }

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
