from typing import Any, List, Optional, Tuple
from app.crud.base import CRUDBase
from app.models.pago_model import PagoModel
from app.schemas.pago_schema import PagoCreate, PagoUpdate

class CRUDPago(CRUDBase[PagoModel, PagoCreate, PagoUpdate]):
    async def get_paginated(
        self, 
        db: Any, 
        page: int = 1, 
        per_page: int = 10, 
        q: Optional[str] = None
    ) -> Tuple[List[PagoModel], int]:
        collection = db[self.collection_name]
        filter_query = {}
        
        # 1. Aplicar Filtros (Búsqueda insensible a mayúsculas)
        if q:
            regex = {"$regex": q, "$options": "i"}
            or_conditions = [
                {"concepto": regex},
                {"estado": regex}
            ]
            
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

pago = CRUDPago(PagoModel, "pagos")
