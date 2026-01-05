from typing import Any, List, Optional, Tuple
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorCollection
from app.crud.base import CRUDBase
from datetime import datetime
from bson import ObjectId
from app.models.libreta_model import LibretaModel, EstadoDocumento
from app.schemas.libreta_schema import LibretaCreate, LibretaUpdate
from app.models.malla_curricular_model import NivelEducativo
from app.models.curso_model import TurnoCurso
from app.schemas.estudiante_schema import GradoFilter
from app.schemas.estudiante_schema import GradoFilter


class CRUDLibreta(CRUDBase[LibretaModel, LibretaCreate, LibretaUpdate]):
    
    async def create(self, db: Any, *, obj_in: LibretaCreate) -> LibretaModel:
        # Use model_dump to preserve ObjectId types instead of jsonable_encoder
        db_obj_data = obj_in.model_dump(exclude_unset=True)
        # Ensure relations are ObjectIds (if Pydantic didn't handle it already, but PyObjectId usually does)
        # In Pydantic V2 model_dump returns python objects (ObjectId) by default.
        
        # Insert
        result = await db[self.collection_name].insert_one(db_obj_data)
        
        # Create model from inserted data + id
        db_obj_data["_id"] = result.inserted_id
        return self.model(**db_obj_data)

    async def update_generic(self, db: Any, *, db_obj: LibretaModel, update_data: dict) -> LibretaModel:
        # Custom update for dict
        if update_data:
            # We assume update_data might come from Form, so values might be strings.
            # Convert specific fields to ObjectId if needed
            if "estudiante_id" in update_data and isinstance(update_data["estudiante_id"], str):
                 if ObjectId.is_valid(update_data["estudiante_id"]):
                     update_data["estudiante_id"] = ObjectId(update_data["estudiante_id"])
            
            # Remove _id from update
            if "_id" in update_data:
                del update_data["_id"]
                
            updated_at = datetime.utcnow()
            update_data["updated_at"] = updated_at
            
            await db[self.collection_name].update_one(
                {"_id": db_obj.id},
                {"$set": update_data}
            )
            return await self.get(db, id=db_obj.id)
        return db_obj
    
    async def get_paginated(
        self, 
        db: Any, 
        page: int = 1, 
        per_page: int = 10, 
        q: Optional[str] = None,
        filters: Optional[dict] = None, # New generic filters (RBAC)
        nivel: Optional[NivelEducativo] = None,
        grado: Optional[GradoFilter] = None,
        turno: Optional[TurnoCurso] = None,
        paralelo: Optional[str] = None,
        estado_documento: Optional[EstadoDocumento] = None
    ) -> Tuple[List[LibretaModel], int]:
        collection = db[self.collection_name]
        filter_query = filters.copy() if filters else {}
        
        # 1. Filtro General (Titulo or Gestion)
        if q:
            regex = {"$regex": q, "$options": "i"}
            or_conditions = [
                {"titulo": regex},
            ]
            if q.isdigit():
                or_conditions.append({"gestion": int(q)})
            
            if "$or" in filter_query:
                 # If we already have an OR for some reason, we need to be careful, but usually we don't.
                 # Let's combine using $and if necessary, but for now simple merge.
                 pass 
            else:
                 filter_query["$or"] = or_conditions

        # 2. Filtro Estado
        if estado_documento:
            filter_query["estado_documento"] = estado_documento

        # 3. Filtros Avanzados (Requiere buscar Estudiantes primero)
        if nivel or grado or turno or paralelo:
            # Reutilizamos lógica de curso/malla
            curso_query = {}
            if nivel: curso_query["nivel"] = nivel
            if turno: curso_query["turno"] = turno
            if paralelo: curso_query["paralelo"] = paralelo
            
            if grado:
                malla_query = {}
                anio_map = {
                    GradoFilter.PRE_KINDER: 1, GradoFilter.KINDER: 2,
                    GradoFilter.PRIMERO: 1, GradoFilter.SEGUNDO: 2,
                    GradoFilter.TERCERO: 3, GradoFilter.CUARTO: 4,
                    GradoFilter.QUINTO: 5, GradoFilter.SEXTO: 6,
                    # Secundaria
                    GradoFilter.PRIMERO_SEC: 1, GradoFilter.SEGUNDO_SEC: 2,
                    GradoFilter.TERCERO_SEC: 3, GradoFilter.CUARTO_SEC: 4,
                    GradoFilter.QUINTO_SEC: 5, GradoFilter.SEXTO_SEC: 6
                }
                
                # Handling secondary if it was passed generically, but assuming primary flow for now
                if grado in anio_map:
                    malla_query["anio_escolaridad"] = anio_map[grado]
                
                if grado in [GradoFilter.PRE_KINDER, GradoFilter.KINDER]:
                    malla_query["nivel"] = NivelEducativo.INICIAL.value
                    curso_query["nivel"] = NivelEducativo.INICIAL.value
                elif nivel:
                    malla_query["nivel"] = nivel.value
                    
                mallas = await db["mallas_curriculares"].find(malla_query, projection={"_id": 1}).to_list(100)
                malla_ids = [m["_id"] for m in mallas]
                if not malla_ids: return [], 0
                curso_query["malla_id"] = {"$in": malla_ids}

            cursos = await db["cursos"].find(curso_query, projection={"_id": 1}).to_list(1000)
            curso_ids = [c["_id"] for c in cursos]
            
            if not curso_ids:
                return [], 0
                
            # Buscar estudiantes en esos cursos
            estudiantes = await db["estudiantes"].find({"curso_id": {"$in": curso_ids}}, projection={"_id": 1}).to_list(10000)
            estudiante_ids = [e["_id"] for e in estudiantes]
            
            if not estudiante_ids:
                return [], 0
            
            # Combine with existing estudiante_id filter from RBAC if present
            if "estudiante_id" in filter_query:
                 # Calculate intersection
                 existing_ids = filter_query["estudiante_id"].get("$in", [])
                 # convert all to str for intersection safety
                 existing_strs = set(str(sid) for sid in existing_ids)
                 new_strs = set(str(sid) for sid in estudiante_ids)
                 intersection = existing_strs.intersection(new_strs)
                 
                 if not intersection:
                     return [], 0
                 
                 # We need to preserve ObjectId type if original was ObjectId
                 # Simplest approach: use the intersection list converted back to ObjectId if needed, 
                 # but our lookup uses ObjectIds.
                 filter_query["estudiante_id"] = {"$in": [ObjectId(sid) for sid in intersection]}
            else:
                filter_query["estudiante_id"] = {"$in": estudiante_ids}

        # Query Final
        total_count = await collection.count_documents(filter_query)
        skip = (page - 1) * per_page
        cursor = collection.find(filter_query).skip(skip).limit(per_page)
        
        results = []
        async for doc in cursor:
            results.append(self.model(**doc))
            
        return results, total_count

libreta = CRUDLibreta(LibretaModel, "libretas")
