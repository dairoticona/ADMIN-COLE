from typing import List
from fastapi import APIRouter, HTTPException
from app.crud.crud_malla import malla as crud_malla
from app.schemas.malla_curricular_schema import MallaCurricularCreate, MallaCurricularUpdate, MallaCurricularResponse

from app.core.database import get_database

router = APIRouter()

@router.get("/", response_model=List[MallaCurricularResponse])
async def read_mallas(skip: int = 0, limit: int = 100):
    db = get_database()
    return await crud_malla.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=MallaCurricularResponse)
async def create_malla(malla_in: MallaCurricularCreate):
    db = get_database()
    return await crud_malla.create(db, obj_in=malla_in)

@router.get("/{id}", response_model=MallaCurricularResponse)
async def read_malla(id: str):
    db = get_database()
    malla = await crud_malla.get(db, id=id)
    if not malla:
        raise HTTPException(status_code=404, detail="Malla Curricular not found")
    return malla

@router.put("/{id}", response_model=MallaCurricularResponse)
async def update_malla(id: str, malla_in: MallaCurricularUpdate):
    db = get_database()
    malla = await crud_malla.get(db, id=id)
    if not malla:
        raise HTTPException(status_code=404, detail="Malla Curricular not found")
    return await crud_malla.update(db, db_obj=malla, obj_in=malla_in)

@router.delete("/{id}", response_model=MallaCurricularResponse)
async def delete_malla(id: str):
    db = get_database()
    malla = await crud_malla.get(db, id=id)
    if not malla:
        raise HTTPException(status_code=404, detail="Malla Curricular not found")
    return await crud_malla.remove(db, id=id)
