from typing import List
from fastapi import APIRouter, HTTPException
from app.crud.crud_pago import pago as crud_pago
from app.schemas.pago_schema import PagoCreate, PagoUpdate, PagoResponse

from app.core.database import get_database

router = APIRouter()

@router.get("/", response_model=List[PagoResponse])
async def read_pagos(skip: int = 0, limit: int = 100):
    db = get_database()
    return await crud_pago.get_multi(db, skip=skip, limit=limit)

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
