from app.crud.base import CRUDBase
from app.models.pago_model import PagoModel
from app.schemas.pago_schema import PagoCreate, PagoUpdate

class CRUDPago(CRUDBase[PagoModel, PagoCreate, PagoUpdate]):
    pass

pago = CRUDPago(PagoModel, "pagos")
