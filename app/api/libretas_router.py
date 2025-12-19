import os
import shutil
import uuid
from typing import List, Optional
import math
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, status
from app.crud.crud_libreta import libreta as crud_libreta
from app.schemas.libreta_schema import LibretaCreate, LibretaUpdate, LibretaResponse
from app.schemas.common import PaginatedResponse
from app.core.database import get_database
from app.models.libreta_model import EstadoDocumento
from app.models.malla_curricular_model import NivelEducativo
from app.models.curso_model import TurnoCurso
from app.schemas.estudiante_schema import GradoFilter

router = APIRouter()

UPLOAD_DIR = "uploads/libretas"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=PaginatedResponse[LibretaResponse])
async def read_libretas(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    q: Optional[str] = None,
    nivel: Optional[NivelEducativo] = Query(None, description="Filtro por Nivel Educativo"),
    grado: Optional[GradoFilter] = Query(None, description="Filtro por Grado"),
    turno: Optional[TurnoCurso] = Query(None, description="Filtro por Turno"),
    paralelo: Optional[str] = Query(None, description="Filtro por Paralelo (A, B, etc)"),
    estado_documento: Optional[EstadoDocumento] = Query(None, description="Estado del documento")
):
    db = get_database()
    items, total = await crud_libreta.get_paginated(
        db, 
        page=page, 
        per_page=per_page, 
        q=q,
        nivel=nivel,
        grado=grado,
        turno=turno,
        paralelo=paralelo,
        estado_documento=estado_documento
    )
    
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": items
    }

@router.post("/", response_model=LibretaResponse)
async def create_libreta(
    estudiante_id: str = Form(...),
    gestion: int = Form(...),
    titulo: Optional[str] = Form(None),
    estado_documento: EstadoDocumento = Form(EstadoDocumento.BORRADOR),
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    # Guardar archivo
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    libreta_in = LibretaCreate(
        estudiante_id=estudiante_id,
        gestion=gestion,
        titulo=titulo,
        estado_documento=estado_documento
    )
    
    # Manually adding the file path that isn't in the base API model usually or handled via extra dict
    # Since crud.create takes obj_in, we'll pass a dict to metadata
    db = get_database()
    return await crud_libreta.create_with_file(db, obj_in=libreta_in, file_path=file_path)

@router.get("/{id}", response_model=LibretaResponse)
async def read_libreta(id: str):
    db = get_database()
    libreta = await crud_libreta.get(db, id=id)
    if not libreta:
        raise HTTPException(status_code=404, detail="Libreta not found")
    return libreta

@router.put("/{id}", response_model=LibretaResponse)
async def update_libreta(
    id: str,
    estudiante_id: Optional[str] = Form(None),
    gestion: Optional[int] = Form(None),
    titulo: Optional[str] = Form(None),
    estado_documento: Optional[EstadoDocumento] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    db = get_database()
    libreta_db = await crud_libreta.get(db, id=id)
    if not libreta_db:
        raise HTTPException(status_code=404, detail="Libreta not found")

    new_file_path = None
    if file:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
        
        filename = f"{uuid.uuid4()}_{file.filename}"
        new_file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(new_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Opcional: Borrar archivo viejo si existe
        # if libreta_db.archivo_path and os.path.exists(libreta_db.archivo_path):
        #     os.remove(libreta_db.archivo_path)

    # Construir objeto update
    update_data = {}
    if estudiante_id: update_data["estudiante_id"] = estudiante_id
    if gestion: update_data["gestion"] = gestion
    if titulo: update_data["titulo"] = titulo
    if estado_documento: update_data["estado_documento"] = estado_documento
    if new_file_path: update_data["archivo_path"] = new_file_path

    # Usamos LibretaUpdate solo para validación parcial si quisiéramos, pero aquí construimos dict
    return await crud_libreta.update_generic(db, db_obj=libreta_db, update_data=update_data)

@router.delete("/{id}", response_model=LibretaResponse)
async def delete_libreta(id: str):
    db = get_database()
    libreta = await crud_libreta.get(db, id=id)
    if not libreta:
        raise HTTPException(status_code=404, detail="Libreta not found")
        
    # Opcional: Borrar archivo físico
    if libreta.archivo_path and os.path.exists(libreta.archivo_path):
        try:
            os.remove(libreta.archivo_path)
        except:
            pass
            
    return await crud_libreta.remove(db, id=id)
