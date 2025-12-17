from typing import Any, List, Optional, Tuple
from app.crud.base import CRUDBase
from app.models.estudiante_model import EstudianteModel
from app.schemas.estudiante_schema import EstudianteCreate, EstudianteUpdate
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.malla_curricular_model import NivelEducativo
from app.models.curso_model import TurnoCurso
from app.schemas.estudiante_schema import GradoFilter

class CRUDEstudiante(CRUDBase[EstudianteModel, EstudianteCreate, EstudianteUpdate]):
    async def get_multi_paginated(
        self, 
        db: Any, 
        *, 
        page: int = 1, 
        per_page: int = 10, 
        q: Optional[str] = None,
        nivel: Optional[NivelEducativo] = None,
        grado: Optional[GradoFilter] = None,
        turno: Optional[TurnoCurso] = None,
        paralelo: Optional[str] = None
    ) -> Tuple[List[EstudianteModel], int]:
        collection: AsyncIOMotorCollection = db[self.collection_name]
        
        # 1. Base Filter (Search)
        filter_query = {}
        if q:
            regex = {"$regex": q, "$options": "i"}
            or_conditions = [
                {"nombres": regex},
                {"apellidos": regex},
            ]
            if q.isdigit():
                or_conditions.append({"rude": int(q)})
            filter_query["$or"] = or_conditions

        # 2. Advanced Filters (Requires joining/looking up Cursos and Mallas)
        # If any of these filters are present, we need to find the valid curso_ids first
        if nivel or grado or turno or paralelo:
            curso_query = {}
            
            # Direct filters on Curso
            if nivel:
                curso_query["nivel"] = nivel
            if turno:
                curso_query["turno"] = turno
            if paralelo:
                curso_query["paralelo"] = paralelo
            
            # Grado filter (requires Malla lookup)
            if grado:
                malla_query = {}
                anio_map = {
                    GradoFilter.PRE_KINDER: 1,
                    GradoFilter.KINDER: 2,
                    GradoFilter.PRIMERO: 1,
                    GradoFilter.SEGUNDO: 2,
                    GradoFilter.TERCERO: 3,
                    GradoFilter.CUARTO: 4,
                    GradoFilter.QUINTO: 5,
                    GradoFilter.SEXTO: 6
                }
                
                # Set anio_escolaridad
                if grado in anio_map:
                    malla_query["anio_escolaridad"] = anio_map[grado]

                # Special logic for Initial
                if grado in [GradoFilter.PRE_KINDER, GradoFilter.KINDER]:
                    malla_query["nivel"] = NivelEducativo.INICIAL.value
                    # Also enforce it on curso_query to be safe/consistent
                    curso_query["nivel"] = NivelEducativo.INICIAL.value
                elif nivel:
                    # If grado is basic (1-6) and nivel is specified, ensure match in malla
                    malla_query["nivel"] = nivel.value

                # Find valid mallas
                mallas_cursor = db["mallas_curriculares"].find(malla_query, projection={"_id": 1})
                malla_ids = [doc["_id"] for doc in await mallas_cursor.to_list(length=100)]
                
                if not malla_ids:
                    # If no mallas match (e.g. "8vo de Primaria" which doesn't exist), return empty
                    return [], 0
                
                curso_query["malla_id"] = {"$in": malla_ids}

            # Find valid cursos
            cursos_cursor = db["cursos"].find(curso_query, projection={"_id": 1})
            curso_ids = [doc["_id"] for doc in await cursos_cursor.to_list(length=1000)]
            
            if not curso_ids:
                 return [], 0
            
            # Add to main filter
            # If we already have criteria (like search), we use $and
            # But here we can just add the field to the dictionary since keys are unique
            filter_query["curso_id"] = {"$in": curso_ids}

        total_count = await collection.count_documents(filter_query)
        
        skip = (page - 1) * per_page
        cursor = collection.find(filter_query).skip(skip).limit(per_page)
        
        results = []
        async for doc in cursor:
            results.append(self.model(**doc))
            
        return results, total_count

estudiante = CRUDEstudiante(EstudianteModel, "estudiantes")
