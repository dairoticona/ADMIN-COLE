from typing import List, Optional
import math
from fastapi import APIRouter, HTTPException, Query
from app.crud.crud_pago import pago as crud_pago
from app.schemas.pago_schema import PagoCreate, PagoUpdate, PagoResponse
from app.schemas.common import PaginatedResponse
from app.core.database import get_database

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[PagoResponse])
async def read_pagos(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    q: Optional[str] = None
):
    db = get_database()
    items, total = await crud_pago.get_paginated(db, page=page, per_page=per_page, q=q)
    
    # Calcular total de páginas
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": items
    }

@router.post("/", response_model=PagoResponse)
async def create_pago(pago_in: PagoCreate):
    db = get_database()
    pago = await crud_pago.create(db, obj_in=pago_in)
    
    # === ENVIAR NOTIFICACIÓN A TODOS LOS ADMINS SI HAY COMPROBANTE ===
    # Solo notificar si el pago tiene comprobante (padre subió evidencia)
    if pago.get("comprobante"):
        from app.crud.crud_notificacion import notificacion as crud_notificacion
        from app.models.common import UserRole
        from bson import ObjectId
        
        try:
            # Obtener información del estudiante y padre para el mensaje
            estudiante_id = pago.get("estudiante_id")
            padre_id = pago.get("padre_id")
            concepto = pago.get("concepto", "pago")
            monto = pago.get("monto", 0)
            
            estudiante_nombre = "un estudiante"
            padre_nombre = "un padre"
            
            if estudiante_id:
                estudiante = await db["estudiantes"].find_one({"_id": ObjectId(estudiante_id) if isinstance(estudiante_id, str) else estudiante_id})
                if estudiante:
                    estudiante_nombre = f"{estudiante.get('nombre', '')} {estudiante.get('apellido', '')}".strip()
            
            if padre_id:
                padre = await db["users"].find_one({"_id": ObjectId(padre_id) if isinstance(padre_id, str) else padre_id})
                if padre:
                    padre_nombre = f"{padre.get('nombre', '')} {padre.get('apellido', '')}".strip()
            
            # Obtener todos los admins activos
            users_collection = db["users"]
            admin_users = []
            
            cursor = users_collection.find({"role": UserRole.ADMIN, "is_active": True})
            async for admin in cursor:
                admin_users.append(admin)
            
            if admin_users:
                # Crear notificaciones para todos los admins
                notifications_to_create = []
                for admin in admin_users:
                    notif_data = {
                        "type": "payment_submitted",
                        "title": "Nuevo Comprobante de Pago 💰",
                        "message": f"{padre_nombre} ha registrado un pago de Bs. {monto:.2f} para {estudiante_nombre} ({concepto})",
                        "user_id": admin["_id"],
                        "related_id": ObjectId(pago["_id"]) if isinstance(pago.get("_id"), str) else pago.get("_id")
                    }
                    notifications_to_create.append(notif_data)
                
                await crud_notificacion.create_many(db, notifications_to_create)
        except Exception as e:
            # No fallar si las notificaciones fallan, solo registrar
            print(f"Error al crear notificaciones de pago: {e}")
    
    return pago


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


@router.post("/{id}/aprobar", response_model=PagoResponse)
async def aprobar_pago(id: str):
    """Aprobar un pago (cambiar estado a PAGADO)"""
    from bson import ObjectId
    from datetime import datetime
    
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID de pago inválido")
    
    db = get_database()
    collection = db["pagos"]
    
    # Verificar que el pago existe
    pago = await collection.find_one({"_id": ObjectId(id)})
    
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    # Actualizar el estado a PAGADO y la fecha de resolución
    update_data = {
        "estado": "PAGADO",
        "updated_at": datetime.utcnow()
    }
    
    # Actualizar fecha de resolución en el comprobante si existe
    if pago.get("comprobante"):
        update_data["comprobante.fecha_resolucion"] = datetime.utcnow()
    
    await collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )
    
    # === ENVIAR NOTIFICACIÓN AL PADRE ===
    from app.crud.crud_notificacion import notificacion as crud_notificacion
    
    padre_id = pago.get("padre_id")
    if padre_id:
        # Obtener información del estudiante para el mensaje
        estudiante_id = pago.get("estudiante_id")
        concepto = pago.get("concepto", "pago")
        monto = pago.get("monto", 0)
        estudiante_nombre = "su hijo/a"
        
        if estudiante_id:
            estudiante = await db["estudiantes"].find_one({"_id": estudiante_id})
            if estudiante:
                estudiante_nombre = f"{estudiante.get('nombre', '')} {estudiante.get('apellido', '')}".strip()
        
        notif_data = {
            "type": "payment_approved",
            "title": "Pago Aprobado ✅",
            "message": f"El pago de Bs. {monto:.2f} para {estudiante_nombre} ({concepto}) ha sido aprobado.",
            "user_id": padre_id,
            "related_id": ObjectId(id)
        }
        
        try:
            await crud_notificacion.create(db, notif_data)
        except Exception as e:
            print(f"Error al crear notificación: {e}")
    
    # Obtener y retornar el pago actualizado
    updated_pago = await collection.find_one({"_id": ObjectId(id)})
    updated_pago["_id"] = str(updated_pago["_id"])
    
    return updated_pago


@router.post("/{id}/rechazar", response_model=PagoResponse)
async def rechazar_pago(id: str):
    """Rechazar un pago (cambiar estado a RECHAZADO)"""
    from bson import ObjectId
    from datetime import datetime
    
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID de pago inválido")
    
    db = get_database()
    collection = db["pagos"]
    
    # Verificar que el pago existe
    pago = await collection.find_one({"_id": ObjectId(id)})
    
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    # Actualizar el estado a RECHAZADO y la fecha de resolución
    update_data = {
        "estado": "RECHAZADO",
        "updated_at": datetime.utcnow()
    }
    
    # Actualizar fecha de resolución en el comprobante si existe
    if pago.get("comprobante"):
        update_data["comprobante.fecha_resolucion"] = datetime.utcnow()
    
    await collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )
    
    # === ENVIAR NOTIFICACIÓN AL PADRE ===
    from app.crud.crud_notificacion import notificacion as crud_notificacion
    
    padre_id = pago.get("padre_id")
    if padre_id:
        # Obtener información del estudiante para el mensaje
        estudiante_id = pago.get("estudiante_id")
        concepto = pago.get("concepto", "pago")
        monto = pago.get("monto", 0)
        estudiante_nombre = "su hijo/a"
        
        if estudiante_id:
            estudiante = await db["estudiantes"].find_one({"_id": estudiante_id})
            if estudiante:
                estudiante_nombre = f"{estudiante.get('nombre', '')} {estudiante.get('apellido', '')}".strip()
        
        notif_data = {
            "type": "payment_rejected",
            "title": "Pago Rechazado ❌",
            "message": f"El pago de Bs. {monto:.2f} para {estudiante_nombre} ({concepto}) ha sido rechazado. Por favor, verifique el comprobante.",
            "user_id": padre_id,
            "related_id": ObjectId(id)
        }
        
        try:
            await crud_notificacion.create(db, notif_data)
        except Exception as e:
            print(f"Error al crear notificación: {e}")
    
    # Obtener y retornar el pago actualizado
    updated_pago = await collection.find_one({"_id": ObjectId(id)})
    updated_pago["_id"] = str(updated_pago["_id"])
    
    return updated_pago

