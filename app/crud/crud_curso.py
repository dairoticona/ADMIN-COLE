from app.crud.base import CRUDBase
from app.models.curso_model import CursoModel
from app.schemas.curso_schema import CursoCreate, CursoUpdate

class CRUDCurso(CRUDBase[CursoModel, CursoCreate, CursoUpdate]):
    pass

curso = CRUDCurso(CursoModel, "cursos")
