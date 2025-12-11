from app.crud.base import CRUDBase
from app.models.libreta_model import LibretaModel
from app.schemas.libreta_schema import LibretaCreate, LibretaUpdate

class CRUDLibreta(CRUDBase[LibretaModel, LibretaCreate, LibretaUpdate]):
    pass

libreta = CRUDLibreta(LibretaModel, "libretas")
