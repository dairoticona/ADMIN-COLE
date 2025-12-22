from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.common import PyObjectId, UserRole

# --- Schemas ---

# Generic User Response used by Auth (/me) and Admin (listing users)
class AuthUserResponse(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    email: EmailStr
    role: UserRole
    nombre: str
    apellido: str
    username: Optional[str] = None 
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Campos opcionales que pueden venir o no
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    hijos_ids: Optional[List[PyObjectId]] = []

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

class Token(BaseModel):
    access_token: str
    token_type: str
    user: AuthUserResponse # Update to use proper schema for serialization
    
class LoginRequest(BaseModel):
    username: str
    password: str
