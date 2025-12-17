from typing import Any, List, Optional, Tuple
from app.crud.base import CRUDBase
from app.models.libreta_model import LibretaModel
from app.schemas.libreta_schema import LibretaCreate, LibretaUpdate

class CRUDLibreta(CRUDBase[LibretaModel, LibretaCreate, LibretaUpdate]):
    async def get_paginated(
        self, 
        db: Any, 
        page: int = 1, 
        per_page: int = 10, 
        q: Optional[str] = None
    ) -> Tuple[List[LibretaModel], int]:
        collection = db[self.collection_name]
        filter_query = {}
        
        # 1. Aplicar Filtros (Búsqueda insensible a mayúsculas)
        if q:
            regex = {"$regex": q, "$options": "i"}
            or_conditions = [
                {"estado_final": regex},
                {"datos_institucionales.nombre_colegio": regex},
                {"datos_institucionales.sie": regex},
                {"datos_institucionales.distrito": regex}
            ]
            
            # Si es número, buscar en gestion
            if q.isdigit():
                or_conditions.append({"gestion": int(q)})
                
            filter_query = {"$or": or_conditions}

        # 2. Obtener Total (CRÍTICO para calcular páginas)
        total_count = await collection.count_documents(filter_query)
        
        # 3. Aplicar Paginación (Skip & Limit)
        skip = (page - 1) * per_page
        cursor = collection.find(filter_query).skip(skip).limit(per_page)
        
        results = []
        async for doc in cursor:
            results.append(self.model(**doc))
            
        return results, total_count

libreta = CRUDLibreta(LibretaModel, "libretas")
