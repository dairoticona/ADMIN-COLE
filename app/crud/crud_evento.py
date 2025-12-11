from app.crud.base import CRUDBase
from app.models.evento_model import EventoModel
from app.schemas.evento_schema import EventoCreate, EventoUpdate

class CRUDEvento(CRUDBase[EventoModel, EventoCreate, EventoUpdate]):
    pass

evento = CRUDEvento(EventoModel, "eventos")
