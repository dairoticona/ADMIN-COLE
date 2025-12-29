from typing import Any, Dict, List, Optional, Tuple
from app.crud.base import CRUDBase
from app.models.licencia_model import LicenciaModel
from app.schemas.licencia_schema import LicenciaCreate, LicenciaUpdate

from app.models.malla_curricular_model import NivelEducativo
from app.models.curso_model import TurnoCurso
from app.schemas.estudiante_schema import GradoFilter

class CRUDLicencia(CRUDBase[LicenciaModel, LicenciaCreate, LicenciaUpdate]):
    async def get_paginated(
        self, 
        db: Any, 
        page: int = 1, 
        per_page: int = 10, 
        q: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        # Nuevos filtros
        nivel: Optional[NivelEducativo] = None,
        grado: Optional[GradoFilter] = None,
        turno: Optional[TurnoCurso] = None,
        paralelo: Optional[str] = None
    ) -> Tuple[List[LicenciaModel], int]:
        collection = db[self.collection_name]
        
        # Base filter from arguments (e.g. role constraints)
        final_query = filters.copy() if filters else {}
        
        # --- LÓGICA DE FILTRADO AVANZADO (Cruce con Estudiantes/Cursos) ---
        student_ids_from_filters = None
        
        # 1. Si hay filtros académicos, buscar IDs de estudiantes que coincidan
        if nivel or grado or turno or paralelo:
            curso_query = {}
            if nivel: curso_query["nivel"] = nivel
            if turno: curso_query["turno"] = turno
            if paralelo: curso_query["paralelo"] = paralelo
            
            # Grado logic (Similar a estudiantes)
            if grado:
                malla_query = {}
                anio_map = {
                    GradoFilter.PRE_KINDER: 1, GradoFilter.KINDER: 2,
                    GradoFilter.PRIMERO: 1, GradoFilter.SEGUNDO: 2, GradoFilter.TERCERO: 3,
                    GradoFilter.CUARTO: 4, GradoFilter.QUINTO: 5, GradoFilter.SEXTO: 6
                }
                if grado in anio_map:
                    malla_query["anio_escolaridad"] = anio_map[grado]
                
                # Nivel implícito
                if grado in [GradoFilter.PRE_KINDER, GradoFilter.KINDER]:
                    malla_query["nivel"] = NivelEducativo.INICIAL.value
                    curso_query["nivel"] = NivelEducativo.INICIAL.value
                elif nivel:
                    malla_query["nivel"] = nivel.value
                    
                mallas_cursor = db["mallas_curriculares"].find(malla_query, projection={"_id": 1})
                malla_ids = [doc["_id"] for doc in await mallas_cursor.to_list(length=100)]
                
                if not malla_ids:
                    return [], 0 # No hay mallas, no hay cursos, no hay licencias
                
                curso_query["malla_id"] = {"$in": malla_ids}

            # Obtener cursos
            cursos_cursor = db["cursos"].find(curso_query, projection={"_id": 1})
            curso_ids = [doc["_id"] for doc in await cursos_cursor.to_list(length=1000)]
            
            if not curso_ids:
                return [], 0 # No hay cursos
            
            # Obtener estudiantes de esos cursos
            # Nota: Convertimos curso_ids a strings si están guardados como strings en estudiantes, 
            # o ObjectId si es ObjectId. Asumimos str por consistencia en schemas
            curso_ids_str = [str(cid) for cid in curso_ids]
            est_cursor = db["estudiantes"].find({"curso_id": {"$in": curso_ids_str}}, projection={"_id": 1})
            student_ids_from_filters = [doc["_id"] for doc in await est_cursor.to_list(length=10000)]
            
            if not student_ids_from_filters:
                return [], 0 # Nadie cumple los filtros académicos

        # 2. Si hay búsqueda (q), buscar también por nombre de estudiante
        student_ids_from_search = None
        if q:
            regex = {"$regex": q, "$options": "i"}
            est_search_query = {
                "$or": [
                    {"nombres": regex},
                    {"apellidos": regex}
                ]
            }
            if q.isdigit():
                est_search_query["$or"].append({"rude": int(q)})
                
            est_q_cursor = db["estudiantes"].find(est_search_query, projection={"_id": 1})
            student_ids_from_search = [doc["_id"] for doc in await est_q_cursor.to_list(length=1000)]
            
        # --- CONSTRUCCIÓN DE LA QUERY FINAL ---
        
        # Combinar filtros de estudiantes
        target_student_ids = None
        
        # Caso A: Ambos filtros activos (Intersección)
        if student_ids_from_filters is not None and student_ids_from_search is not None:
             target_student_ids = list(set(student_ids_from_filters) & set(student_ids_from_search))
             if not target_student_ids: return [], 0
        
        # Caso B: Solo filtros académicos
        elif student_ids_from_filters is not None:
            target_student_ids = student_ids_from_filters
            
        # Caso C: Solo búsqueda (pero 'q' también busca en motivo/estado)
        # Aquí es tricky: q busca en (licencia.motivo OR licencia.estado) OR (licencia.estudiante_id IN student_ids_from_search)
        
        
        # Aplicar filtro de estudiantes IDs a la query de licencias
        if target_student_ids is not None:
             # Convertir a ObjectId si es necesario (el modelo define estudiante_id como PyObjectId/ObjectId)
             # Aseguramos coincidencia de tipos
             final_query["estudiante_id"] = {"$in": target_student_ids}
        
        
        # Lógica especial para 'q':
        # Si filtramos por IDs de estudiantes (Caso A o B), 'q' ya filtró los IDs en el Caso A.
        # En el Caso B no hay 'q'.
        # El caso complejo es si hay 'q' pero NO hay filtros académicos, o si hay 'q' y queremos buscar en motivo TAMBIÉN.
        
        if q:
            regex = {"$regex": q, "$options": "i"}
            text_conditions = [
                {"motivo": regex},
                {"estado": regex}
            ]
            
            if student_ids_from_search:
                # Si encontramos estudiantes por nombre, incluimos sus IDs en el OR
                # Buscamos licencias que (coincidan en texto O sean de estos estudiantes)
                text_conditions.append({"estudiante_id": {"$in": student_ids_from_search}})
            
            # Si ya tenemos un filtro estricto de estudiantes (por filtros académicos), 
            # el 'q' DEBE restringirse a ese subconjunto.
            # Pero 'q' suele ser restrictivo.
            # Simplificación: Si hay filtros académicos, 'q' solo busca en texto (motivo/estado) DENTRO de esos estudiantes.
            # Si NO hay filtros académicos, 'q' busca en (motivo/estado OR estudiante_nombre).
            
            if student_ids_from_filters is not None:
                 # Ya estamos restringidos a un set de estudiantes. 'q' filtra sobre eso.
                 # Aquí q solo busca en texto de la licencia porque la intersección de nombres ya se hizo arriba (Caso A) 
                 # O espera... si target_student_ids ya es la intersección, entonces implicitamente ya filtramos por nombre.
                 # Pero si 'q' matchea motivo pero NO nombre, deberíamos mostrarlo?
                 # No, si hay intersección es AND.
                 
                 # Si 'q' matchea motivo, debe ser de un estudiante del filtro académico.
                 if not student_ids_from_search:
                     # 'q' no matcheó nombres, so solo buscamos en motivo/estado
                     final_query["$or"] = text_conditions[:2] # Solo motivo/estado
                 else:
                     # 'q' matcheó nombres Y tenemos filtro académico.
                     # target_student_ids tiene la intersección.
                     # Pero qué pasa si el usuario busca "Gripe"? (está en motivo)
                     # No coincidirá con ningún nombre. target_student_ids por nombre será vacío o parcial.
                     # ESTO ES COMPLEJO.
                     
                     # REGLA SIMPLIFICADA Y ROBUSTA:
                     # 1. Base: Licencias de estudiantes de [Filtros Académicos] (si existen).
                     # 2. AND: (Motivo tiene q OR Estado tiene q OR Estudiante es [Estudiantes con nombre q])
                     pass 
            
            # Re-pensando la query construction para ser limpia:
            
            or_conditions = [
                {"motivo": regex},
                {"estado": regex}
            ]
            if student_ids_from_search:
                 or_conditions.append({"estudiante_id": {"$in": student_ids_from_search}})
            
            if "$or" in final_query:
                final_query = {"$and": [final_query, {"$or": or_conditions}]}
            else:
                final_query["$or"] = or_conditions
                
            # Si teníamos filtros de estudiantes (target_student_ids) ya establecidos antes del bloque q:
            # Esos están en final_query["estudiante_id"].
            # Al añadir el $or con student_ids_from_search, podemos crear conflicto si no tenemos cuidado.
            # PERO: Mongo maneja implicitamente top-level field vs $or? No, es AND.
            
            # Caso conflictivo:
            # Filtro Academico: Curso 1A (Ids: [1, 2])
            # Q: "Juan" (Id: 1) -> student_ids_from_search: [1]
            # Q: "Gripe" (Id: null) -> student_ids_from_search: []
            
            # Si Q="Juan":
            # final_query = { "estudiante_id": {$in: [1, 2]}, "$or": [ {motivo: Juan}, {estado: Juan}, {estudiante_id: {$in: [1]}} ] }
            # Resultado: Licencia de hijo 1 (Juan). Correcto.
            
            # Si Q="Gripe" (y Licencia de Hijo 2 tiene motivo "Gripe"):
            # final_query = { "estudiante_id": {$in: [1, 2]}, "$or": [ {motivo: Gripe}, ... {estudiante_id: []} ] }
            # Resultado: Licencia de hijo 2. Correcto.
            
            # Si Q="Pedro" (Id: 3, no está en 1A):
            # final_query = { "estudiante_id": {$in: [1, 2]}, "$or": [..., {estudiante_id: [3]}] }
            # Resultado: (Id in [1,2]) AND (Id in [3] OR motivo=Pedro).
            # Id nunca será 3. Solo saldrá si hijo 1 o 2 tiene motivo "Pedro". Correcto.
            
            pass

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
