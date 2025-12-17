from typing import List, Optional
import math
from fastapi import APIRouter, HTTPException, Query
from app.crud.crud_pago import pago as crud_pago
from app.schemas.pago_schema import PagoCreate, PagoUpdate, PagoResponse
from app.schemas.common import PaginatedResponse
from app.core.database import get_database

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[PagoResponse])
async def read_pagos(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    q: Optional[str] = None
):
    db = get_database()
    items, total = await crud_pago.get_paginated(db, page=page, per_page=per_page, q=q)
    
    # Calcular total de páginas
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": items
    }

@router.post("/", response_model=PagoResponse)
async def create_pago(pago_in: PagoCreate):
    db = get_database()
    return await crud_pago.create(db, obj_in=pago_in)

@router.get("/{id}", response_model=PagoResponse)
async def read_pago(id: str):
    db = get_database()
    pago = await crud_pago.get(db, id=id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago not found")
    return pago

@router.put("/{id}", response_model=PagoResponse)
async def update_pago(id: str, pago_in: PagoUpdate):
    db = get_database()
    pago = await crud_pago.get(db, id=id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago not found")
    return await crud_pago.update(db, db_obj=pago, obj_in=pago_in)

@router.delete("/{id}", response_model=PagoResponse)
async def delete_pago(id: str):
    db = get_database()
    pago = await crud_pago.get(db, id=id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago not found")
    return await crud_pago.remove(db, id=id)
