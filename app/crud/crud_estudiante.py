from typing import Any, List, Optional, Tuple
from app.crud.base import CRUDBase
from app.models.estudiante_model import EstudianteModel
from app.schemas.estudiante_schema import EstudianteCreate, EstudianteUpdate
from motor.motor_asyncio import AsyncIOMotorCollection

class CRUDEstudiante(CRUDBase[EstudianteModel, EstudianteCreate, EstudianteUpdate]):
    async def get_multi_paginated(
        self, 
        db: Any, 
        *, 
        page: int = 1, 
        per_page: int = 10, 
        q: Optional[str] = None
    ) -> Tuple[List[EstudianteModel], int]:
        collection: AsyncIOMotorCollection = db[self.collection_name]
        
        filter_query = {}
        if q:
            regex = {"$regex": q, "$options": "i"}
            or_conditions = [
                {"nombres": regex},
                {"apellidos": regex},
            ]
            # Try to search by rude if q looks like a number
            if q.isdigit():
                # Note: rude is int, so we search exact match
                or_conditions.append({"rude": int(q)})
            
            filter_query = {"$or": or_conditions}

        total_count = await collection.count_documents(filter_query)
        
        skip = (page - 1) * per_page
        cursor = collection.find(filter_query).skip(skip).limit(per_page)
        
        results = []
        async for doc in cursor:
            results.append(self.model(**doc))
            
        return results, total_count

estudiante = CRUDEstudiante(EstudianteModel, "estudiantes")
