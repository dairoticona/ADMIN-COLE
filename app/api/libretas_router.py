import os
import shutil
import uuid
from typing import List, Optional
import math
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, status, Depends
from bson import ObjectId

from app.crud.crud_libreta import libreta as crud_libreta
from app.schemas.libreta_schema import LibretaCreate, LibretaUpdate, LibretaResponse
from app.schemas.common import PaginatedResponse
from app.core.database import get_database
from app.models.libreta_model import EstadoDocumento
from app.models.malla_curricular_model import NivelEducativo
from app.models.curso_model import TurnoCurso
from app.schemas.estudiante_schema import GradoFilter
from app.models.common import UserRole

# Auth & Cloudinary
from app.api.auth_router import get_current_user, get_current_admin
from app.core.cloudinary_service import upload_image, delete_image

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[LibretaResponse])
async def read_libretas(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    q: Optional[str] = None,
    nivel: Optional[NivelEducativo] = Query(None, description="Filtro por Nivel Educativo"),
    grado: Optional[GradoFilter] = Query(None, description="Filtro por Grado"),
    turno: Optional[TurnoCurso] = Query(None, description="Filtro por Turno"),
    paralelo: Optional[str] = Query(None, description="Filtro por Paralelo (A, B, etc)"),
    estado_documento: Optional[EstadoDocumento] = Query(None, description="Estado del documento"),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar libretas.
    - Admins: Ven todo.
    - Padres: Ven solo las de sus hijos.
    """
    db = get_database()
    
    rbac_filters = {}
    if current_user["role"] != UserRole.ADMIN:
        # Parents only see their children
        user_hijos_ids = current_user.get("hijos_ids", [])
        if not user_hijos_ids:
             return {
                "total": 0, "page": page, "per_page": per_page, "total_pages": 0, "data": []
            }
        
        # Ensure ObjectIds
        hijos_oids = [ObjectId(hid) if isinstance(hid, str) else hid for hid in user_hijos_ids]
        rbac_filters["estudiante_id"] = {"$in": hijos_oids}
        
        # Non-admins can only see PUBLISHED report cards usually? 
        # Or maybe drafts if it's discussed? 
        # Typically parents only see PUBLICADA.
        if not estado_documento:
             rbac_filters["estado_documento"] = EstadoDocumento.PUBLICADA
    
    items, total = await crud_libreta.get_paginated(
        db, 
        page=page, 
        per_page=per_page, 
        q=q,
        filters=rbac_filters,
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
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_admin) # Only Admins
):
    """
    Subir libreta (PDF o Imagen). Solo Admins.
    """
    # 1. Validar archivo
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types and not any(file.filename.lower().endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png"]):
         raise HTTPException(status_code=400, detail="Formato no permitido. Use PDF, JPG o PNG.")
         
    # 2. Subir a Cloudinary
    content = await file.read()
    if len(content) > 10 * 1024 * 1024: # 10MB limit
         raise HTTPException(status_code=400, detail="Archivo muy grande (Max 10MB)")
         
    upload_result = await upload_image(content, folder="libretas")
    if not upload_result.get("success"):
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {upload_result.get('error')}")
    
    file_url = upload_result.get("url")

    # 3. Crear en BD
    libreta_in = LibretaCreate(
        estudiante_id=estudiante_id,
        gestion=gestion,
        titulo=titulo,
        estado_documento=estado_documento,
        archivo_path=file_url # Reuse this field for URL
    )
    
    db = get_database()
    return await crud_libreta.create(db, obj_in=libreta_in)

@router.get("/{id}", response_model=LibretaResponse)
async def read_libreta(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    libreta = await crud_libreta.get(db, id=id)
    if not libreta:
        raise HTTPException(status_code=404, detail="Libreta not found")
    
    # Check permissions
    if current_user["role"] != UserRole.ADMIN:
        # Check against children
        user_hijos_ids = [str(x) for x in current_user.get("hijos_ids", [])]
        if str(libreta.estudiante_id) not in user_hijos_ids:
             raise HTTPException(status_code=403, detail="No tiene permiso para ver esta libreta")
    
    return libreta

@router.put("/{id}", response_model=LibretaResponse)
async def update_libreta(
    id: str,
    estudiante_id: Optional[str] = Form(None),
    gestion: Optional[int] = Form(None),
    titulo: Optional[str] = Form(None),
    estado_documento: Optional[EstadoDocumento] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_admin) # Only Admins
):
    db = get_database()
    libreta_db = await crud_libreta.get(db, id=id)
    if not libreta_db:
        raise HTTPException(status_code=404, detail="Libreta not found")

    new_file_url = None
    if file:
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types and not any(file.filename.lower().endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png"]):
            raise HTTPException(status_code=400, detail="Formato no permitido. Use PDF, JPG o PNG.")
        
        content = await file.read()
        upload_result = await upload_image(content, folder="libretas")
        if not upload_result.get("success"):
            raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {upload_result.get('error')}")
            
        new_file_url = upload_result.get("url")
        
    # Construir objeto update
    update_data = {}
    if estudiante_id: update_data["estudiante_id"] = estudiante_id
    if gestion: update_data["gestion"] = gestion
    if titulo: update_data["titulo"] = titulo
    if estado_documento: update_data["estado_documento"] = estado_documento
    if new_file_url: update_data["archivo_path"] = new_file_url

    return await crud_libreta.update_generic(db, db_obj=libreta_db, update_data=update_data)

@router.delete("/{id}", response_model=LibretaResponse)
async def delete_libreta(
    id: str,
    current_user: dict = Depends(get_current_admin)
):
    db = get_database()
    libreta = await crud_libreta.get(db, id=id)
    if not libreta:
        raise HTTPException(status_code=404, detail="Libreta not found")
        
    # Optional: Delete from Cloudinary?
    # We don't store Public ID easily in this model (just URL), so skipping for now unless we parse it.
    # Cloudinary URLs usually: .../upload/.../folder/public_id.ext
    
    return await crud_libreta.remove(db, id=id)
