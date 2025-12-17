from typing import Any, Dict, List, Optional, Tuple
from app.crud.base import CRUDBase
from app.models.licencia_model import LicenciaModel
from app.schemas.licencia_schema import LicenciaCreate, LicenciaUpdate

class CRUDLicencia(CRUDBase[LicenciaModel, LicenciaCreate, LicenciaUpdate]):
    async def get_paginated(
        self, 
        db: Any, 
        page: int = 1, 
        per_page: int = 10, 
        q: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[LicenciaModel], int]:
        collection = db[self.collection_name]
        
        # Base filter from arguments (e.g. role constraints)
        final_query = filters.copy() if filters else {}
        
        # 1. Aplicar Búsqueda por Texto (q)
        if q:
            regex = {"$regex": q, "$options": "i"}
            or_conditions = [
                {"motivo": regex},
                {"estado": regex}
            ]
            
            # Combine strict filters with search query using $and
            if final_query:
                final_query = {
                    "$and": [
                        final_query,
                        {"$or": or_conditions}
                    ]
                }
            else:
                final_query = {"$or": or_conditions}

        # 2. Obtener Total (CRÍTICO para calcular páginas)
        total_count = await collection.count_documents(final_query)
        
        # 3. Aplicar Paginación (Skip & Limit)
        skip = (page - 1) * per_page
        cursor = collection.find(final_query).skip(skip).limit(per_page).sort("created_at", -1)
        
        results = []
        async for doc in cursor:
            results.append(self.model(**doc))
            
        return results, total_count

licencia = CRUDLicencia(LicenciaModel, "licencias")
