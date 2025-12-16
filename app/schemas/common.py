from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    total: int = Field(..., description="Total de registros encontrados")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Registros por página")
    total_pages: int = Field(..., description="Total de páginas")
    data: List[T] = Field(..., description="Lista de objetos")
