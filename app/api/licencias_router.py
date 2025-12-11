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
    
    # Validar que el estudiante_id sea válido
    if not ObjectId.is_valid(licencia_data.estudiante_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de estudiante inválido"
        )
    
    # Verificar que el estudiante existe en la colección 'estudiantes'
    estudiantes_collection = db["estudiantes"]
    estudiante = await estudiantes_collection.find_one({"_id": ObjectId(licencia_data.estudiante_id)})
    
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudiante no encontrado"
        )
    
    # Verificar que el estudiante pertenezca al padre autenticado (usando hijos_ids del usuario)
    # Nota: current_user["hijos_ids"] es una lista de strings
    user_hijos_ids = current_user.get("hijos_ids", [])
    if str(estudiante["_id"]) not in user_hijos_ids:
        # Fallback por si la relación no está sincronizada en User, verificamos por lógica de negocio
        # Pero si 'padres_ids' fue eliminado de Estudiante, dependemos de User.hijos_ids.
        # Asumimos que user_hijos_ids es la fuente de verdad.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear licencias para este estudiante"
        )
    
    licencias_collection = db["licencias"]
    
    # Crear el documento de licencia
    licencia_dict = licencia_data.model_dump()
    
    # Auto-rellenar el padre_id con el usuario actual si no coincide (forzar autoría)
    licencia_dict["padre_id"] = current_user["_id"]
    
    # Convertir enums a strings
    if "estado" in licencia_dict and hasattr(licencia_dict["estado"], "value"):
        licencia_dict["estado"] = licencia_dict["estado"].value
        
    # Convertir date a datetime para MongoDB
    if isinstance(licencia_dict["fecha_inicio"], date) and not isinstance(licencia_dict["fecha_inicio"], datetime):
        licencia_dict["fecha_inicio"] = datetime.combine(licencia_dict["fecha_inicio"], datetime.min.time())
    if isinstance(licencia_dict["fecha_fin"], date) and not isinstance(licencia_dict["fecha_fin"], datetime):
        licencia_dict["fecha_fin"] = datetime.combine(licencia_dict["fecha_fin"], datetime.min.time())

    # Establecer estado inicial como PENDIENTE
    licencia_dict["estado"] = "PENDIENTE"
    
    licencia_dict["created_at"] = datetime.utcnow()
    licencia_dict["updated_at"] = datetime.utcnow()
    
    result = await licencias_collection.insert_one(licencia_dict)
    
    # Retornar la licencia creada
    licencia_dict["_id"] = str(result.inserted_id)
    # Convertir fechas de vuelta a date para la respuesta
    if isinstance(licencia_dict["fecha_inicio"], datetime):
        licencia_dict["fecha_inicio"] = licencia_dict["fecha_inicio"].date()
    if isinstance(licencia_dict["fecha_fin"], datetime):
        licencia_dict["fecha_fin"] = licencia_dict["fecha_fin"].date()
    
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
        # Los padres solo ven sus propias licencias (filtrar por padre_id)
        # Asegurarse de usar el ObjectId correcto
        filter_query = {"padre_id": ObjectId(current_user["_id"]) if isinstance(current_user["_id"], str) else current_user["_id"]}
        # Nota: Si en la DB se guardó como string, esto fallaría. 
        # Pero insertamos usando ObjectId si viene del modelo, o string si pydantic.
        # LicenciaModel define padre_id como PyObjectId, asi que en mongo es ObjectId.
    
    licencias = await collection.find(filter_query).to_list(length=None)
    
    # Convertir ObjectId a string y fechas a date
    for licencia in licencias:
        licencia["_id"] = str(licencia["_id"])
        if "fecha_inicio" in licencia and isinstance(licencia["fecha_inicio"], datetime):
            licencia["fecha_inicio"] = licencia["fecha_inicio"].date()
        if "fecha_fin" in licencia and isinstance(licencia["fecha_fin"], datetime):
            licencia["fecha_fin"] = licencia["fecha_fin"].date()
    
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
        # Comparar ObjectId con ObjectId
        licencia_padre_id = licencia.get("padre_id")
        user_id = current_user["_id"]
        
        # Normalizar a string para comparar
        if str(licencia_padre_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver esta licencia"
            )
    
    licencia["_id"] = str(licencia["_id"])
    if "fecha_inicio" in licencia and isinstance(licencia["fecha_inicio"], datetime):
        licencia["fecha_inicio"] = licencia["fecha_inicio"].date()
    if "fecha_fin" in licencia and isinstance(licencia["fecha_fin"], datetime):
        licencia["fecha_fin"] = licencia["fecha_fin"].date()
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
    
    # Verificar permisos
    if current_user["role"] != UserRole.ADMIN:
        if str(licencia.get("padre_id")) != str(current_user["_id"]):
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
        # Convertir enums a strings
        if "estado" in update_data and hasattr(update_data["estado"], "value"):
            update_data["estado"] = update_data["estado"].value
            
        # Convertir date a datetime
        if "fecha_inicio" in update_data and isinstance(update_data["fecha_inicio"], date) and not isinstance(update_data["fecha_inicio"], datetime):
            update_data["fecha_inicio"] = datetime.combine(update_data["fecha_inicio"], datetime.min.time())
        if "fecha_fin" in update_data and isinstance(update_data["fecha_fin"], date) and not isinstance(update_data["fecha_fin"], datetime):
            update_data["fecha_fin"] = datetime.combine(update_data["fecha_fin"], datetime.min.time())
        
        update_data["updated_at"] = datetime.utcnow()
        await collection.update_one(
            {"_id": ObjectId(licencia_id)},
            {"$set": update_data}
        )
    
    # Obtener y retornar la licencia actualizada
    updated_licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    updated_licencia["_id"] = str(updated_licencia["_id"])
    if "fecha_inicio" in updated_licencia and isinstance(updated_licencia["fecha_inicio"], datetime):
        updated_licencia["fecha_inicio"] = updated_licencia["fecha_inicio"].date()
    if "fecha_fin" in updated_licencia and isinstance(updated_licencia["fecha_fin"], datetime):
        updated_licencia["fecha_fin"] = updated_licencia["fecha_fin"].date()
    
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
    
    # Verificar permisos
    if current_user["role"] != UserRole.ADMIN:
        if str(licencia.get("padre_id")) != str(current_user["_id"]):
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
    
    # Actualizar el estado a APROBADA
    await collection.update_one(
        {"_id": ObjectId(licencia_id)},
        {"$set": {"estado": "APROBADA", "updated_at": datetime.utcnow()}}
    )
    
    updated_licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    updated_licencia["_id"] = str(updated_licencia["_id"])
    if "fecha_inicio" in updated_licencia and isinstance(updated_licencia["fecha_inicio"], datetime):
        updated_licencia["fecha_inicio"] = updated_licencia["fecha_inicio"].date()
    if "fecha_fin" in updated_licencia and isinstance(updated_licencia["fecha_fin"], datetime):
        updated_licencia["fecha_fin"] = updated_licencia["fecha_fin"].date()
    
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
    
    updated_licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    updated_licencia["_id"] = str(updated_licencia["_id"])
    if "fecha_inicio" in updated_licencia and isinstance(updated_licencia["fecha_inicio"], datetime):
        updated_licencia["fecha_inicio"] = updated_licencia["fecha_inicio"].date()
    if "fecha_fin" in updated_licencia and isinstance(updated_licencia["fecha_fin"], datetime):
        updated_licencia["fecha_fin"] = updated_licencia["fecha_fin"].date()
    
    return updated_licencia
