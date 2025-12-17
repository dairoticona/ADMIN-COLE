from typing import Any, Dict, Optional, Union, List, Tuple
from app.crud.base import CRUDBase
from app.models.papa_model import PapaModel
from app.schemas.papa_schema import PapaCreate, PapaUpdate

class CRUDPapa(CRUDBase[PapaModel, PapaCreate, PapaUpdate]):
    async def get_by_email(self, db: Any, *, email: str) -> Optional[PapaModel]:
        # We access "users" collection because Papas are users
        collection = db[self.collection_name]
        doc = await collection.find_one({"email": email})
        if doc:
            return self.model(**doc)
        return None

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
        q: Optional[str] = None
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
            
            # Combine base filter with OR conditions
            filter_query["$or"] = or_conditions

        # 2. Obtener Total (CRÍTICO para calcular páginas)
        total_count = await collection.count_documents(filter_query)
        
        # 3. Aplicar Paginación (Skip & Limit)
        skip = (page - 1) * per_page
        cursor = collection.find(filter_query).skip(skip).limit(per_page).sort("created_at", -1)
        
        results = []
        async for doc in cursor:
            results.append(self.model(**doc))
            
        return results, total_count

# Instance pointing to "users" collection
papa = CRUDPapa(PapaModel, "users")
