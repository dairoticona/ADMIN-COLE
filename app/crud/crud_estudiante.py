from app.crud.base import CRUDBase
from app.models.estudiante_model import EstudianteModel
from app.schemas.estudiante_schema import EstudianteCreate, EstudianteUpdate

class CRUDEstudiante(CRUDBase[EstudianteModel, EstudianteCreate, EstudianteUpdate]):
    pass

estudiante = CRUDEstudiante(EstudianteModel, "estudiantes")
