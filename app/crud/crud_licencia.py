from app.crud.base import CRUDBase
from app.models.licencia_model import LicenciaModel
from app.schemas.licencia_schema import LicenciaCreate, LicenciaUpdate

class CRUDLicencia(CRUDBase[LicenciaModel, LicenciaCreate, LicenciaUpdate]):
    pass

licencia = CRUDLicencia(LicenciaModel, "licencias")
