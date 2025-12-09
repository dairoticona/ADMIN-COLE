from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime, date
from bson import ObjectId

from app.core.database import get_database
from app.models.user_model import UserRole
from app.schemas.licencia_schema import LicenciaCreate, LicenciaUpdate, LicenciaResponse
from app.api.auth_router import get_current_user, get_current_admin

router = APIRouter()


@router.post("/", response_model=LicenciaResponse, status_code=status.HTTP_201_CREATED)
async def create_licencia(
    licencia_data: LicenciaCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear una nueva licencia (solo padres pueden crear licencias)"""
    # Verificar que el usuario sea un padre
    if current_user["role"] != UserRole.PADRE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los padres pueden crear licencias"
        )
    
    db = get_database()
    collection = db["licencias"]
    
    # Crear el documento de licencia
    licencia_dict = licencia_data.model_dump()
    
    # Convertir enums a strings
    licencia_dict["tipo_permiso"] = licencia_dict["tipo_permiso"].value if hasattr(licencia_dict["tipo_permiso"], "value") else licencia_dict["tipo_permiso"]
    licencia_dict["grado_estudiante"] = licencia_dict["grado_estudiante"].value if hasattr(licencia_dict["grado_estudiante"], "value") else licencia_dict["grado_estudiante"]
    
    # Convertir date a datetime para MongoDB
    if isinstance(licencia_dict["fecha"], date) and not isinstance(licencia_dict["fecha"], datetime):
        licencia_dict["fecha"] = datetime.combine(licencia_dict["fecha"], datetime.min.time())
    
    # Auto-rellenar el nombre del padre desde el usuario autenticado
    licencia_dict["nombre_padre"] = f"{current_user.get('nombre', '')} {current_user.get('apellido', '')}".strip()
    if not licencia_dict["nombre_padre"]:
        licencia_dict["nombre_padre"] = current_user["username"]
    
    # Establecer estado inicial como PENDIENTE
    licencia_dict["estado"] = "PENDIENTE"
    
    licencia_dict["created_at"] = datetime.utcnow()
    licencia_dict["updated_at"] = datetime.utcnow()
    
    result = await collection.insert_one(licencia_dict)
    
    # Retornar la licencia creada
    licencia_dict["_id"] = str(result.inserted_id)
    # Convertir fecha de vuelta a date para la respuesta
    if isinstance(licencia_dict["fecha"], datetime):
        licencia_dict["fecha"] = licencia_dict["fecha"].date()
    
    return licencia_dict


@router.get("/", response_model=List[LicenciaResponse])
async def list_licencias(current_user: dict = Depends(get_current_user)):
    """
    Listar licencias:
    - Administradores ven todas las licencias
    - Padres solo ven sus propias licencias
    """
    db = get_database()
    collection = db["licencias"]
    
    # Construir el filtro según el rol del usuario
    if current_user["role"] == UserRole.ADMIN:
        # Los administradores ven todas las licencias
        filter_query = {}
    else:
        # Los padres solo ven sus propias licencias
        nombre_padre = f"{current_user.get('nombre', '')} {current_user.get('apellido', '')}".strip()
        if not nombre_padre:
            nombre_padre = current_user["username"]
        filter_query = {"nombre_padre": nombre_padre}
    
    licencias = await collection.find(filter_query).to_list(length=None)
    
    # Convertir ObjectId a string y fecha a date
    for licencia in licencias:
        licencia["_id"] = str(licencia["_id"])
        # Convertir fecha de datetime a date si es necesario
        if "fecha" in licencia and isinstance(licencia["fecha"], datetime):
            licencia["fecha"] = licencia["fecha"].date()
    
    return licencias


@router.get("/{licencia_id}", response_model=LicenciaResponse)
async def get_licencia(
    licencia_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener una licencia específica por ID"""
    if not ObjectId.is_valid(licencia_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de licencia inválido"
        )
    
    db = get_database()
    collection = db["licencias"]
    
    licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    
    if not licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )
    
    # Verificar permisos: solo el padre propietario o un admin pueden ver la licencia
    if current_user["role"] != UserRole.ADMIN:
        nombre_padre = f"{current_user.get('nombre', '')} {current_user.get('apellido', '')}".strip()
        if not nombre_padre:
            nombre_padre = current_user["username"]
        
        if licencia["nombre_padre"] != nombre_padre:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver esta licencia"
            )
    
    licencia["_id"] = str(licencia["_id"])
    # Convertir fecha de datetime a date si es necesario
    if "fecha" in licencia and isinstance(licencia["fecha"], datetime):
        licencia["fecha"] = licencia["fecha"].date()
    return licencia


@router.put("/{licencia_id}", response_model=LicenciaResponse)
async def update_licencia(
    licencia_id: str,
    licencia_data: LicenciaUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Actualizar una licencia existente"""
    if not ObjectId.is_valid(licencia_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de licencia inválido"
        )
    
    db = get_database()
    collection = db["licencias"]
    
    # Verificar que la licencia existe
    licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    
    if not licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )
    
    # Verificar permisos: solo el padre propietario o un admin pueden actualizar
    if current_user["role"] != UserRole.ADMIN:
        nombre_padre = f"{current_user.get('nombre', '')} {current_user.get('apellido', '')}".strip()
        if not nombre_padre:
            nombre_padre = current_user["username"]
        
        if licencia["nombre_padre"] != nombre_padre:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para actualizar esta licencia"
            )
        
        # Los padres solo pueden actualizar licencias PENDIENTES
        if licencia.get("estado") != "PENDIENTE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puede actualizar licencias en estado PENDIENTE"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = licencia_data.model_dump(exclude_unset=True)
    
    if update_data:
        # Convertir enums a strings si están presentes
        if "tipo_permiso" in update_data:
            update_data["tipo_permiso"] = update_data["tipo_permiso"].value if hasattr(update_data["tipo_permiso"], "value") else update_data["tipo_permiso"]
        if "grado_estudiante" in update_data:
            update_data["grado_estudiante"] = update_data["grado_estudiante"].value if hasattr(update_data["grado_estudiante"], "value") else update_data["grado_estudiante"]
        
        # Convertir date a datetime para MongoDB si está presente
        if "fecha" in update_data and isinstance(update_data["fecha"], date) and not isinstance(update_data["fecha"], datetime):
            update_data["fecha"] = datetime.combine(update_data["fecha"], datetime.min.time())
        
        update_data["updated_at"] = datetime.utcnow()
        await collection.update_one(
            {"_id": ObjectId(licencia_id)},
            {"$set": update_data}
        )
    
    # Obtener y retornar la licencia actualizada
    updated_licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    updated_licencia["_id"] = str(updated_licencia["_id"])
    # Convertir fecha de datetime a date si es necesario
    if "fecha" in updated_licencia and isinstance(updated_licencia["fecha"], datetime):
        updated_licencia["fecha"] = updated_licencia["fecha"].date()
    
    return updated_licencia


@router.delete("/{licencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_licencia(
    licencia_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Eliminar una licencia"""
    if not ObjectId.is_valid(licencia_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de licencia inválido"
        )
    
    db = get_database()
    collection = db["licencias"]
    
    # Verificar que la licencia existe
    licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    
    if not licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )
    
    # Verificar permisos: solo el padre propietario o un admin pueden eliminar
    if current_user["role"] != UserRole.ADMIN:
        nombre_padre = f"{current_user.get('nombre', '')} {current_user.get('apellido', '')}".strip()
        if not nombre_padre:
            nombre_padre = current_user["username"]
        
        if licencia["nombre_padre"] != nombre_padre:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para eliminar esta licencia"
            )
    
    # Eliminar la licencia
    await collection.delete_one({"_id": ObjectId(licencia_id)})
    
    return None


@router.post("/{licencia_id}/aprobar", response_model=LicenciaResponse)
async def aprobar_licencia(
    licencia_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Aprobar una licencia (solo administradores)"""
    if not ObjectId.is_valid(licencia_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de licencia inválido"
        )
    
    db = get_database()
    collection = db["licencias"]
    
    # Verificar que la licencia existe
    licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    
    if not licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )
    
    # Actualizar el estado a ACEPTADA
    await collection.update_one(
        {"_id": ObjectId(licencia_id)},
        {"$set": {"estado": "ACEPTADA", "updated_at": datetime.utcnow()}}
    )
    
    # Obtener y retornar la licencia actualizada
    updated_licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    updated_licencia["_id"] = str(updated_licencia["_id"])
    # Convertir fecha de datetime a date si es necesario
    if "fecha" in updated_licencia and isinstance(updated_licencia["fecha"], datetime):
        updated_licencia["fecha"] = updated_licencia["fecha"].date()
    
    return updated_licencia


@router.post("/{licencia_id}/rechazar", response_model=LicenciaResponse)
async def rechazar_licencia(
    licencia_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Rechazar una licencia (solo administradores)"""
    if not ObjectId.is_valid(licencia_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de licencia inválido"
        )
    
    db = get_database()
    collection = db["licencias"]
    
    # Verificar que la licencia existe
    licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    
    if not licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )
    
    # Actualizar el estado a RECHAZADA
    await collection.update_one(
        {"_id": ObjectId(licencia_id)},
        {"$set": {"estado": "RECHAZADA", "updated_at": datetime.utcnow()}}
    )
    
    # Obtener y retornar la licencia actualizada
    updated_licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    updated_licencia["_id"] = str(updated_licencia["_id"])
    # Convertir fecha de datetime a date si es necesario
    if "fecha" in updated_licencia and isinstance(updated_licencia["fecha"], datetime):
        updated_licencia["fecha"] = updated_licencia["fecha"].date()
    
    return updated_licencia
