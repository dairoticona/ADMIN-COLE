from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from typing import List
from bson import ObjectId

from app.core.database import get_database
from app.core.database import get_database
from app.models.common import UserRole
from app.schemas.auth_schemas import AuthUserResponse
from app.schemas.admin_schemas import (
    AdminCreateRequest, 
    ChangePasswordRequest, 
    UpdateProfileRequest
)
from app.api.auth_router import get_current_admin
from app.core.security import get_password_hash, verify_password

router = APIRouter()

@router.post("/create-admin", response_model=AuthUserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_data: AdminCreateRequest, 
    current_user: dict = Depends(get_current_admin)
):
    """Crear un nuevo administrador (Solo para administradores)"""
    db = get_database()
    collection = db["users"]
    
    # Check if user exists
    existing_user = await collection.find_one({"username": admin_data.username})
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario con este username ya existe"
        )
    
    # Create admin document
    user_dict = admin_data.model_dump(exclude={"password"})
    
    # Generar datos automáticos
    user_dict["email"] = f"admin_{admin_data.username}@admincole.com"
    user_dict["nombre"] = "Admin"
    user_dict["apellido"] = admin_data.username
    
    user_dict["hashed_password"] = get_password_hash(admin_data.password)
    user_dict["role"] = UserRole.ADMIN
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    user_dict["is_active"] = True
    user_dict["is_superuser"] = False
    
    result = await collection.insert_one(user_dict)
    
    # Return created user
    user_dict["_id"] = str(result.inserted_id)
    return user_dict

@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_admin)
):
    """Cambiar contraseña propia (Solo administradores)"""
    db = get_database()
    collection = db["users"]
    
    # Verificar contraseña actual
    if not verify_password(password_data.old_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    new_hashed_password = get_password_hash(password_data.new_password)
    
    await collection.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": {
            "hashed_password": new_hashed_password,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Contraseña actualizada correctamente"}

@router.put("/update-profile", response_model=AuthUserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_admin)
):
    """Actualizar nombre de usuario propio (Solo administradores)"""
    db = get_database()
    collection = db["users"]
    
    # Verificar si el nuevo username ya existe (y no es el mismo usuario)
    if profile_data.username != current_user["username"]:
        existing_user = await collection.find_one({"username": profile_data.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este nombre de usuario ya está en uso"
            )
    
    update_data = {"username": profile_data.username}
    update_data["updated_at"] = datetime.utcnow()
    
    await collection.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": update_data}
    )
    
    # Obtener usuario actualizado
    updated_user = await collection.find_one({"_id": ObjectId(current_user["_id"])})
    updated_user["_id"] = str(updated_user["_id"])
    
    return updated_user

@router.get("/users", response_model=List[AuthUserResponse])
async def get_all_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: dict = Depends(get_current_admin)
):
    """Listar todos los usuarios (Solo administradores)"""
    db = get_database()
    collection = db["users"]
    
    users = []
    users = []
    cursor = collection.find({"role": UserRole.ADMIN}).skip(skip).limit(limit).sort("created_at", -1)
    
    async for user in cursor:
        user["_id"] = str(user["_id"])
        users.append(user)
    
    return users

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Eliminar un usuario (Solo administradores)"""
    db = get_database()
    collection = db["users"]
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
        
    # Evitar que se elimine a sí mismo
    if user_id == current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta"
        )
    
    # Buscar el usuario antes de eliminar
    user_to_delete = await collection.find_one({"_id": ObjectId(user_id)})
    
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
        
    # Proteger al superadministrador (Brandon)
    if user_to_delete.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede eliminar al superadministrador principal"
        )
    
    # Eliminar el usuario
    await collection.delete_one({"_id": ObjectId(user_id)})
    
    return None
