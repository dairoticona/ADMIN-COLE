from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from typing import Annotated

from app.core.database import get_database
# Removed UserModel usage, relying on direct DB or AuthSchemas
from app.models.common import UserRole
from app.schemas.auth_schemas import (
    AuthUserResponse, 
    Token, 
    AdminLoginRequest,
    PapaLoginRequest
)
from app.core.config import settings
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    oauth2_scheme
)
from jose import jwt, JWTError

router = APIRouter()

from fastapi.security import HTTPAuthorizationCredentials

async def get_current_user(token_auth: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    """Obtener el usuario actual desde el token"""
    token = token_auth.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = get_database()
    collection = db["users"]
    # Buscar por email o username (ya que 'sub' puede ser cualquiera de los dos)
    user = await collection.find_one({
        "$or": [
            {"email": username},
            {"username": username}
        ]
    })
    
    if user is None:
        raise credentials_exception
    
    user["_id"] = str(user["_id"])
    return user

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    """Verificar que el usuario actual es administrador"""
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de administrador"
        )
    return current_user



@router.post("/login/admin", response_model=Token)
async def login_admin(credentials: AdminLoginRequest):
    """Login para Administradores (Username + Password)"""
    db = get_database()
    collection = db["users"]
    
    user = await collection.find_one({"username": credentials.username})
    
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.get("role") != UserRole.ADMIN:
        raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="No tiene permisos de administrador"
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Para admin usamos username como sub
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, 
        expires_delta=access_token_expires
    )
    
    user["_id"] = str(user["_id"])
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }

@router.post("/login/padre", response_model=Token)
async def login_padre(credentials: PapaLoginRequest):
    """Login para Padres (Email + Password)"""
    db = get_database()
    collection = db["users"]
    
    user = await collection.find_one({"email": credentials.email})
    
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if user.get("role") != UserRole.PADRE:
        raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="No tiene acceso como padre. Use el login de administrador."
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Para padres usamos email como sub
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}, 
        expires_delta=access_token_expires
    )
    
    user["_id"] = str(user["_id"])
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=AuthUserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user
