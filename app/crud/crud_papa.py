from typing import Any, Dict, Optional, Union, List, Tuple
from bson import ObjectId
from app.crud.base import CRUDBase
from app.models.papa_model import PapaModel
from app.schemas.papa_schema import PapaCreate, PapaUpdate

from app.models.malla_curricular_model import NivelEducativo
from app.models.curso_model import TurnoCurso
from app.schemas.estudiante_schema import GradoFilter

class CRUDPapa(CRUDBase[PapaModel, PapaCreate, PapaUpdate]):
    async def get_by_email(self, db: Any, *, email: str) -> Optional[PapaModel]:
        # We access "users" collection because Papas are users
        collection = db[self.collection_name]
        doc = await collection.find_one({"email": email})
        if doc:
            return self.model(**doc)
        return None

    async def add_child(self, db: Any, *, papa_id: str, child_id: str) -> Optional[PapaModel]:
        collection = db[self.collection_name]
        
        # Verify student exists? Assuming handled by caller or frontend, 
        # but for safety we could check student existence here or just trust ID.
        # Let's perform the update.
        result = await collection.update_one(
            {"_id": ObjectId(papa_id), "role": "PADRE"},
            {"$addToSet": {"hijos_ids": ObjectId(child_id)}}
        )
        
        if result.modified_count > 0:
            return await self.get(db, id=papa_id)
        
        # If not modified either papa doesn't exist or child already added.
        # Just return current state.
        return await self.get(db, id=papa_id)

    async def remove_child(self, db: Any, *, papa_id: str, child_id: str) -> Optional[PapaModel]:
        collection = db[self.collection_name]
        
        result = await collection.update_one(
            {"_id": ObjectId(papa_id), "role": "PADRE"},
            {"$pull": {"hijos_ids": ObjectId(child_id)}}
        )
        
        if result.modified_count > 0:
            return await self.get(db, id=papa_id)
            
        return await self.get(db, id=papa_id)

    async def create(self, db: Any, *, obj_in: PapaCreate) -> PapaModel:
        # Convert Pydantic model to dict
        obj_in_data = obj_in.model_dump()
        
        # Map 'password' to 'hashed_password' if present
        if "password" in obj_in_data:
            password = obj_in_data.pop("password")
            if password:
                obj_in_data["hashed_password"] = password
        
        # Ensure role is PADRE
        obj_in_data["role"] = "PADRE"
        
        # Set defaults
        if "is_active" not in obj_in_data:
            obj_in_data["is_active"] = True
            
        collection = db[self.collection_name]
        result = await collection.insert_one(obj_in_data)
        
        obj_in_data["_id"] = result.inserted_id
        return self.model(**obj_in_data)

    async def get_paginated(
        self, 
        db: Any, 
        page: int = 1, 
        per_page: int = 10, 
        q: Optional[str] = None,
        nivel: Optional[NivelEducativo] = None,
        grado: Optional[GradoFilter] = None,
        turno: Optional[TurnoCurso] = None,
        paralelo: Optional[str] = None
    ) -> Tuple[List[PapaModel], int]:
        collection = db[self.collection_name]
        
        # Base filter: Must be PADRE
        filter_query = {"role": "PADRE"}
        
        # 1. Aplicar Filtros (Búsqueda insensible a mayúsculas)
        if q:
            regex = {"$regex": q, "$options": "i"}
            or_conditions = [
                {"nombre": regex},
                {"apellido": regex},
                {"email": regex},
                {"telefono": regex}
            ]
            filter_query["$or"] = or_conditions

        # 2. Filtros Avanzados (Join Logic)
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
                    GradoFilter.QUINTO: 5, GradoFilter.SEXTO: 6
                }
                if grado in anio_map:
                    malla_query["anio_escolaridad"] = anio_map[grado]
                
                # Special logic for Initial
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
            
            # Filtrar padres que tengan al menos uno de estos hijos
            filter_query["hijos_ids"] = {"$in": estudiante_ids}

        # 3. Obtener Total (CRÍTICO para calcular páginas)
        total_count = await collection.count_documents(filter_query)
        
        # 4. Aplicar Paginación (Skip & Limit)
        skip = (page - 1) * per_page
        cursor = collection.find(filter_query).skip(skip).limit(per_page).sort("created_at", -1)
        
        results = []
        async for doc in cursor:
            results.append(self.model(**doc))
            
        return results, total_count

# Instance pointing to "users" collection
papa = CRUDPapa(PapaModel, "users")
