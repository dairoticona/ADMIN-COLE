from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.schemas.reunion_schema import ReunionCreate, ReunionUpdate, ReunionResponse
from app.api.auth_router import get_current_user, get_current_admin

router = APIRouter()


@router.post("/", response_model=ReunionResponse, status_code=status.HTTP_201_CREATED)
async def create_reunion(
    reunion_data: ReunionCreate,
    current_user: dict = Depends(get_current_admin)
):
    """Crear una nueva reunión (Solo administradores)"""
    db = get_database()
    collection = db["reuniones"]
    
    # Convertir el modelo a diccionario
    reunion_dict = reunion_data.model_dump()
    reunion_dict["created_at"] = datetime.utcnow()
    reunion_dict["updated_at"] = datetime.utcnow()
    
    # Convertir time a string para almacenar en MongoDB
    reunion_dict["hora_inicio"] = reunion_dict["hora_inicio"].isoformat()
    reunion_dict["hora_conclusion"] = reunion_dict["hora_conclusion"].isoformat()
    
    # Insertar en la base de datos
    result = await collection.insert_one(reunion_dict)
    
    # Retornar la reunión creada
    reunion_dict["_id"] = str(result.inserted_id)
    return reunion_dict


@router.get("/", response_model=List[ReunionResponse])
async def get_all_reuniones(
    skip: int = 0, 
    limit: int = 100,
    current_user: dict = Depends(get_current_admin)
):
    """Obtener todas las reuniones (Solo administradores)"""
    db = get_database()
    collection = db["reuniones"]
    
    reuniones = []
    cursor = collection.find().skip(skip).limit(limit).sort("fecha", -1)
    
    async for reunion in cursor:
        reunion["_id"] = str(reunion["_id"])
        reuniones.append(reunion)
    
    return reuniones


@router.get("/{reunion_id}", response_model=ReunionResponse)
async def get_reunion(
    reunion_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Obtener una reunión por ID (Solo administradores)"""
    db = get_database()
    collection = db["reuniones"]
    
    # Validar ObjectId
    if not ObjectId.is_valid(reunion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reunión inválido"
        )
    
    reunion = await collection.find_one({"_id": ObjectId(reunion_id)})
    
    if not reunion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reunión no encontrada"
        )
    
    reunion["_id"] = str(reunion["_id"])
    return reunion


@router.put("/{reunion_id}", response_model=ReunionResponse)
async def update_reunion(
    reunion_id: str, 
    reunion_data: ReunionUpdate,
    current_user: dict = Depends(get_current_admin)
):
    """Actualizar una reunión (Solo administradores)"""
    db = get_database()
    collection = db["reuniones"]
    
    # Validar ObjectId
    if not ObjectId.is_valid(reunion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reunión inválido"
        )
    
    # Verificar que la reunión existe
    existing_reunion = await collection.find_one({"_id": ObjectId(reunion_id)})
    if not existing_reunion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reunión no encontrada"
        )
    
    # Preparar datos para actualizar (solo campos no nulos)
    update_data = reunion_data.model_dump(exclude_unset=True)
    
    if update_data:
        # Convertir time a string si están presentes
        if "hora_inicio" in update_data:
            update_data["hora_inicio"] = update_data["hora_inicio"].isoformat()
        if "hora_conclusion" in update_data:
            update_data["hora_conclusion"] = update_data["hora_conclusion"].isoformat()
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Actualizar en la base de datos
        await collection.update_one(
            {"_id": ObjectId(reunion_id)},
            {"$set": update_data}
        )
    
    # Obtener y retornar la reunión actualizada
    updated_reunion = await collection.find_one({"_id": ObjectId(reunion_id)})
    updated_reunion["_id"] = str(updated_reunion["_id"])
    return updated_reunion


@router.delete("/{reunion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reunion(
    reunion_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Eliminar una reunión (Solo administradores)"""
    db = get_database()
    collection = db["reuniones"]
    
    # Validar ObjectId
    if not ObjectId.is_valid(reunion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reunión inválido"
        )
    
    # Verificar que la reunión existe
    existing_reunion = await collection.find_one({"_id": ObjectId(reunion_id)})
    if not existing_reunion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reunión no encontrada"
        )
    
    # Eliminar la reunión
    await collection.delete_one({"_id": ObjectId(reunion_id)})
    
    return None
