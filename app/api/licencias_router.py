from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form, Body
from typing import List, Optional, Any
import math
from app.crud.crud_licencia import licencia as crud_licencia
from app.schemas.common import PaginatedResponse
from datetime import datetime, date
from bson import ObjectId

from app.core.database import get_database
from app.core.cloudinary_service import upload_image
from app.models.common import UserRole
from app.models.malla_curricular_model import NivelEducativo
from app.models.curso_model import TurnoCurso
from app.schemas.estudiante_schema import GradoFilter
from app.schemas.licencia_schema import LicenciaCreate, LicenciaUpdate, LicenciaResponse
from app.api.auth_router import get_current_user, get_current_admin

router = APIRouter()




@router.post("/with-file", response_model=LicenciaResponse, status_code=status.HTTP_201_CREATED)
async def create_licencia_with_file(
    estudiante_id: str = Form(..., description="ID del estudiante"),
    tipo_permiso: str = Form(..., description="Tipo de permiso (PERSONAL, MEDICO, FAMILIAR)"),
    fecha_inicio: date = Form(..., description="Fecha de inicio"),
    fecha_fin: date = Form(..., description="Fecha de fin"),
    motivo: Optional[str] = Form(None, description="Motivo de la licencia"),
    file: Optional[UploadFile] = File(None, description="Archivo adjunto (opcional según tipo)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Crear licencia subiendo el archivo en el mismo paso (Multipart).
    """
    # 1. Subir imagen si existe
    adjunto_url = None
    if file:
        # Validaciones de archivo duplicadas de upload_image para seguridad
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Tipo de archivo no permitido. Use jpg, png o pdf")
        
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Archivo muy grande (Max 5MB)")
            
        upload_result = await upload_image(content, folder="licencias")
        if not upload_result.get("success"):
            raise HTTPException(status_code=500, detail=f"Error subiendo imagen: {upload_result.get('error')}")
            
        adjunto_url = upload_result.get("url")

    # 2. Construir modelo LicenciaCreate
    try:
        # Validar el enum de tipo_permiso manualmente o dejar que Pydantic lo haga
        licencia_data = LicenciaCreate(
            estudiante_id=estudiante_id,
            tipo_permiso=tipo_permiso,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            motivo=motivo,
            adjunto=adjunto_url
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 3. Reutilizar lógica de creación (copiada para mantener contexto de dependencias)
    # NOTA: Sería ideal refactorizar la lógica core a un servicio, pero por ahora duplicamos para no romper el original
    
    db = get_database()
    
    # Determinar padre_id
    if current_user["role"] == UserRole.PADRE:
        padre_id = current_user["_id"]
        user_hijos_ids = [str(uid) for uid in current_user.get("hijos_ids", [])]
        if str(licencia_data.estudiante_id) not in user_hijos_ids:
            raise HTTPException(status_code=403, detail="No tiene permisos para este estudiante")
    elif current_user["role"] == UserRole.ADMIN:
        # En este endpoint simplificado, asumimos que el admin lo crea a nombre del padre? 
        # O requerimos padre_id en el form? 
        # Para simplificar y dado que el usuario pidió "padre pueda adjuntar", nos enfocamos en el padre.
        # Si un admin usa esto, requeriría padre_id extra. 
        # Vamos a permitir que el admin lo use pero requeriría agregar padre_id al form.
        # Por ahora, lanzamos error si es admin sin padre_id (que no está en el form actual)
        # O mejor: este endpoint "rápido" es principalmente para padres desde la app.
        raise HTTPException(status_code=400, detail="Este endpoint simplificado es para uso de Padres. Admins usar endpoint estándar.")
    else:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Validaciones DB
    if not ObjectId.is_valid(licencia_data.estudiante_id):
        raise HTTPException(status_code=400, detail="ID estudiante inválido")

    estudiante = await db["estudiantes"].find_one({"_id": ObjectId(licencia_data.estudiante_id)})
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Insertar
    licencia_dict = licencia_data.model_dump(exclude={"padre_id"})
    licencia_dict["padre_id"] = ObjectId(padre_id)
    
    # Conversiones
    if hasattr(licencia_dict.get("estado"), "value"): licencia_dict["estado"] = licencia_dict["estado"].value
    if hasattr(licencia_dict.get("tipo_permiso"), "value"): licencia_dict["tipo_permiso"] = licencia_dict["tipo_permiso"].value
    
    licencia_dict["fecha_inicio"] = datetime.combine(licencia_dict["fecha_inicio"], datetime.min.time())
    licencia_dict["fecha_fin"] = datetime.combine(licencia_dict["fecha_fin"], datetime.min.time())
    licencia_dict["estado"] = "PENDIENTE"
    licencia_dict["created_at"] = datetime.utcnow()
    licencia_dict["updated_at"] = datetime.utcnow()

    res = await db["licencias"].insert_one(licencia_dict)
    
    # Respuesta
    licencia_dict["_id"] = str(res.inserted_id)
    licencia_dict["padre_id"] = str(licencia_dict["padre_id"])
    licencia_dict["fecha_inicio"] = licencia_dict["fecha_inicio"].date()
    licencia_dict["fecha_fin"] = licencia_dict["fecha_fin"].date()

    return licencia_dict

@router.get("/", response_model=PaginatedResponse[LicenciaResponse])
async def list_licencias(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    q: Optional[str] = None,
    # Nuevos filtros
    nivel: Optional[NivelEducativo] = None,
    grado: Optional[GradoFilter] = None,
    turno: Optional[TurnoCurso] = None,
    paralelo: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Listar licencias paginadas:
    - Administradores ven todas las licencias
    - Padres solo ven sus propias licencias
    - Filtros avanzados disponibles (Nivel, Grado, Turno, Paralelo, Búsqueda por nombre)
    """
    db = get_database()
    
    # Construir el filtro según el rol del usuario
    filter_query = {}
    if current_user["role"] != UserRole.ADMIN:
        # Los padres solo ven sus propias licencias (filtrar por padre_id)
        # Asegurarse de usar el ObjectId correcto
        filter_query = {"padre_id": ObjectId(current_user["_id"]) if isinstance(current_user["_id"], str) else current_user["_id"]}
    
    items, total = await crud_licencia.get_paginated(
        db, 
        page=page, 
        per_page=per_page, 
        q=q, 
        filters=filter_query,
        # Pasar nuevos filtros
        nivel=nivel,
        grado=grado,
        turno=turno,
        paralelo=paralelo
    )
    
    # Convertir ObjectId a string y fechas a date
    processed_items = []
    for licencia in items:
        # Pydantic model dump to dict to manipulate fields if needed, 
        # but since we return PaginatedResponse[LicenciaResponse], Pydantic should handle validation if we pass objects.
        # However, our CRUD returns LicenciaModel objects. 
        # If we need exact same processing as before (converting ObjectId to str for response):
        # The Response Model handles serialization of ObjectId -> str usually if configured.
        # Check LicenciaResponse/Model config.
        # But previous code did manual conversion. Let's rely on Pydantic's from_attributes or just pass models.
        # Our BaseModels have json_encoders for ObjectId.
        processed_items.append(licencia)
    
    # Calcular total de páginas
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": processed_items
    }


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
        if "tipo_permiso" in update_data and hasattr(update_data["tipo_permiso"], "value"):
            update_data["tipo_permiso"] = update_data["tipo_permiso"].value
            
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
    
    # === ENVIAR NOTIFICACIÓN AL PADRE ===
    from app.crud.crud_notificacion import notificacion as crud_notificacion
    
    padre_id = licencia.get("padre_id")
    if padre_id:
        # Obtener información del estudiante para el mensaje
        estudiante_id = licencia.get("estudiante_id")
        estudiante_nombre = "su hijo/a"
        
        if estudiante_id:
            estudiante = await db["estudiantes"].find_one({"_id": estudiante_id})
            if estudiante:
                estudiante_nombre = f"{estudiante.get('nombre', '')} {estudiante.get('apellido', '')}".strip()
        
        notif_data = {
            "type": "license_approved",
            "title": "Licencia Aprobada ✅",
            "message": f"La solicitud de licencia para {estudiante_nombre} ha sido aprobada.",
            "user_id": padre_id,
            "related_id": ObjectId(licencia_id)
        }
        
        try:
            await crud_notificacion.create(db, notif_data)
        except Exception as e:
            # No fallar si la notificación falla, solo registrar
            print(f"Error al crear notificación: {e}")
    
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
    
    # === ENVIAR NOTIFICACIÓN AL PADRE ===
    from app.crud.crud_notificacion import notificacion as crud_notificacion
    
    padre_id = licencia.get("padre_id")
    if padre_id:
        # Obtener información del estudiante para el mensaje
        estudiante_id = licencia.get("estudiante_id")
        estudiante_nombre = "su hijo/a"
        
        if estudiante_id:
            estudiante = await db["estudiantes"].find_one({"_id": estudiante_id})
            if estudiante:
                estudiante_nombre = f"{estudiante.get('nombre', '')} {estudiante.get('apellido', '')}".strip()
        
        notif_data = {
            "type": "license_rejected",
            "title": "Licencia Rechazada ❌",
            "message": f"La solicitud de licencia para {estudiante_nombre} ha sido rechazada.",
            "user_id": padre_id,
            "related_id": ObjectId(licencia_id)
        }
        
        try:
            await crud_notificacion.create(db, notif_data)
        except Exception as e:
            # No fallar si la notificación falla, solo registrar
            print(f"Error al crear notificación: {e}")
    
    updated_licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    updated_licencia["_id"] = str(updated_licencia["_id"])
    if "fecha_inicio" in updated_licencia and isinstance(updated_licencia["fecha_inicio"], datetime):
        updated_licencia["fecha_inicio"] = updated_licencia["fecha_inicio"].date()
    if "fecha_fin" in updated_licencia and isinstance(updated_licencia["fecha_fin"], datetime):
        updated_licencia["fecha_fin"] = updated_licencia["fecha_fin"].date()
    
    return updated_licencia



@router.post("/{licencia_id}/comentario", response_model=LicenciaResponse)
async def comentar_licencia(
    licencia_id: str,
    comentario: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_admin)
):
    """
    Agregar un comentario/respuesta del administrador a una licencia.
    Body espera: { "comentario": "Texto..." }
    """
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
    
    # Actualizar la respuesta del admin
    await collection.update_one(
        {"_id": ObjectId(licencia_id)},
        {"$set": {"respuesta_admin": comentario, "updated_at": datetime.utcnow()}}
    )
    
    # === ENVIAR NOTIFICACIÓN AL PADRE ===
    from app.crud.crud_notificacion import notificacion as crud_notificacion
    
    padre_id = licencia.get("padre_id")
    if padre_id:
        # Obtener información del estudiante para el mensaje
        estudiante_id = licencia.get("estudiante_id")
        estudiante_nombre = "su hijo/a"
        
        if estudiante_id:
            estudiante = await db["estudiantes"].find_one({"_id": estudiante_id})
            if estudiante:
                estudiante_nombre = f"{estudiante.get('nombre', '')} {estudiante.get('apellido', '')}".strip()
        
        notif_data = {
            "type": "license_commented",
            "title": "Nuevo Comentario en Licencia 💬",
            "message": f"El administrador ha agregado un comentario a la licencia de {estudiante_nombre}.",
            "user_id": padre_id,
            "related_id": ObjectId(licencia_id)
        }
        
        try:
            await crud_notificacion.create(db, notif_data)
        except Exception as e:
            # No fallar si la notificación falla, solo registrar
            print(f"Error al crear notificación: {e}")
    
    updated_licencia = await collection.find_one({"_id": ObjectId(licencia_id)})
    updated_licencia["_id"] = str(updated_licencia["_id"])
    if "fecha_inicio" in updated_licencia and isinstance(updated_licencia["fecha_inicio"], datetime):
        updated_licencia["fecha_inicio"] = updated_licencia["fecha_inicio"].date()
    if "fecha_fin" in updated_licencia and isinstance(updated_licencia["fecha_fin"], datetime):
        updated_licencia["fecha_fin"] = updated_licencia["fecha_fin"].date()
    
    return updated_licencia

