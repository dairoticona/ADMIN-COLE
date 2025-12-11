from app.crud.base import CRUDBase
from app.models.malla_curricular_model import MallaCurricularModel
from app.schemas.malla_curricular_schema import MallaCurricularCreate, MallaCurricularUpdate

class CRUDMalla(CRUDBase[MallaCurricularModel, MallaCurricularCreate, MallaCurricularUpdate]):
    pass

malla = CRUDMalla(MallaCurricularModel, "mallas_curriculares")
