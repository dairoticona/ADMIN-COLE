from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime, date
from bson import ObjectId

from app.core.database import get_database
from app.models.user_model import UserRole
from app.schemas.hijo_schema import HijoCreate, HijoUpdate, HijoResponse
from app.api.auth_router import get_current_user, get_current_admin

router = APIRouter()


@router.post("/", response_model=HijoResponse, status_code=status.HTTP_201_CREATED)
async def create_hijo(
    hijo_data: HijoCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear un nuevo hijo (solo padres pueden crear hijos)"""
    # Verificar que el usuario sea un padre
    if current_user["role"] != UserRole.PADRE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los padres pueden registrar hijos"
        )
    
    db = get_database()
    collection = db["hijos"]
    
    # Verificar que el RUDE no exista (hijo único en el sistema)
    existing_hijo = await collection.find_one({"rude": hijo_data.rude})
    if existing_hijo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un hijo registrado con el RUDE {hijo_data.rude}"
        )
    
    # Crear el documento del hijo
    hijo_dict = hijo_data.model_dump()
    
    # Convertir enum a string
    hijo_dict["curso"] = hijo_dict["curso"].value if hasattr(hijo_dict["curso"], "value") else hijo_dict["curso"]
    
    # Convertir date a datetime para MongoDB
    if isinstance(hijo_dict["fecha_nacimiento"], date) and not isinstance(hijo_dict["fecha_nacimiento"], datetime):
        hijo_dict["fecha_nacimiento"] = datetime.combine(hijo_dict["fecha_nacimiento"], datetime.min.time())
    
    # Auto-rellenar información del padre desde el usuario autenticado
    hijo_dict["padre_id"] = current_user["_id"]
    hijo_dict["nombre_padre"] = f"{current_user.get('nombre', '')} {current_user.get('apellido', '')}".strip()
    if not hijo_dict["nombre_padre"]:
        hijo_dict["nombre_padre"] = current_user["username"]
    
    hijo_dict["created_at"] = datetime.utcnow()
    hijo_dict["updated_at"] = datetime.utcnow()
    
    result = await collection.insert_one(hijo_dict)
    
    # Retornar el hijo creado
    hijo_dict["_id"] = str(result.inserted_id)
    # Convertir fecha de vuelta a date para la respuesta
    if isinstance(hijo_dict["fecha_nacimiento"], datetime):
        hijo_dict["fecha_nacimiento"] = hijo_dict["fecha_nacimiento"].date()
    
    return hijo_dict


@router.get("/", response_model=List[HijoResponse])
async def list_hijos(current_user: dict = Depends(get_current_user)):
    """
    Listar hijos:
    - Administradores ven todos los hijos
    - Padres solo ven sus propios hijos
    """
    db = get_database()
    collection = db["hijos"]
    
    # Construir el filtro según el rol del usuario
    if current_user["role"] == UserRole.ADMIN:
        # Los administradores ven todos los hijos
        filter_query = {}
    else:
        # Los padres solo ven sus propios hijos
        filter_query = {"padre_id": current_user["_id"]}
    
    hijos = await collection.find(filter_query).to_list(length=None)
    
    # Convertir ObjectId a string y fecha a date
    for hijo in hijos:
        hijo["_id"] = str(hijo["_id"])
        # Convertir fecha de datetime a date si es necesario
        if "fecha_nacimiento" in hijo and isinstance(hijo["fecha_nacimiento"], datetime):
            hijo["fecha_nacimiento"] = hijo["fecha_nacimiento"].date()
    
    return hijos


@router.get("/{hijo_id}", response_model=HijoResponse)
async def get_hijo(
    hijo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener un hijo específico por ID"""
    if not ObjectId.is_valid(hijo_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de hijo inválido"
        )
    
    db = get_database()
    collection = db["hijos"]
    
    hijo = await collection.find_one({"_id": ObjectId(hijo_id)})
    
    if not hijo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hijo no encontrado"
        )
    
    # Verificar permisos: solo el padre propietario o un admin pueden ver el hijo
    if current_user["role"] != UserRole.ADMIN:
        if hijo["padre_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver este hijo"
            )
    
    hijo["_id"] = str(hijo["_id"])
    # Convertir fecha de datetime a date si es necesario
    if "fecha_nacimiento" in hijo and isinstance(hijo["fecha_nacimiento"], datetime):
        hijo["fecha_nacimiento"] = hijo["fecha_nacimiento"].date()
    return hijo


@router.put("/{hijo_id}", response_model=HijoResponse)
async def update_hijo(
    hijo_id: str,
    hijo_data: HijoUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Actualizar un hijo existente"""
    if not ObjectId.is_valid(hijo_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de hijo inválido"
        )
    
    db = get_database()
    collection = db["hijos"]
    
    # Verificar que el hijo existe
    hijo = await collection.find_one({"_id": ObjectId(hijo_id)})
    
    if not hijo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hijo no encontrado"
        )
    
    # Verificar permisos: solo el padre propietario o un admin pueden actualizar
    if current_user["role"] != UserRole.ADMIN:
        if hijo["padre_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para actualizar este hijo"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = hijo_data.model_dump(exclude_unset=True)
    
    if update_data:
        # Si se está actualizando el RUDE, verificar que no exista otro hijo con ese RUDE
        if "rude" in update_data:
            existing_hijo = await collection.find_one({
                "rude": update_data["rude"],
                "_id": {"$ne": ObjectId(hijo_id)}
            })
            if existing_hijo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe otro hijo registrado con el RUDE {update_data['rude']}"
                )
        
        # Convertir enum a string si está presente
        if "curso" in update_data:
            update_data["curso"] = update_data["curso"].value if hasattr(update_data["curso"], "value") else update_data["curso"]
        
        # Convertir date a datetime para MongoDB si está presente
        if "fecha_nacimiento" in update_data and isinstance(update_data["fecha_nacimiento"], date) and not isinstance(update_data["fecha_nacimiento"], datetime):
            update_data["fecha_nacimiento"] = datetime.combine(update_data["fecha_nacimiento"], datetime.min.time())
        
        update_data["updated_at"] = datetime.utcnow()
        await collection.update_one(
            {"_id": ObjectId(hijo_id)},
            {"$set": update_data}
        )
    
    # Obtener y retornar el hijo actualizado
    updated_hijo = await collection.find_one({"_id": ObjectId(hijo_id)})
    updated_hijo["_id"] = str(updated_hijo["_id"])
    # Convertir fecha de datetime a date si es necesario
    if "fecha_nacimiento" in updated_hijo and isinstance(updated_hijo["fecha_nacimiento"], datetime):
        updated_hijo["fecha_nacimiento"] = updated_hijo["fecha_nacimiento"].date()
    
    return updated_hijo


@router.delete("/{hijo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hijo(
    hijo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Eliminar un hijo"""
    if not ObjectId.is_valid(hijo_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de hijo inválido"
        )
    
    db = get_database()
    collection = db["hijos"]
    
    # Verificar que el hijo existe
    hijo = await collection.find_one({"_id": ObjectId(hijo_id)})
    
    if not hijo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hijo no encontrado"
        )
    
    # Verificar permisos: solo el padre propietario o un admin pueden eliminar
    if current_user["role"] != UserRole.ADMIN:
        if hijo["padre_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para eliminar este hijo"
            )
    
    # Eliminar el hijo
    await collection.delete_one({"_id": ObjectId(hijo_id)})
    
    return None
