from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from typing import Annotated

from app.core.database import get_database
from app.models.user_model import UserModel, UserRole
from app.schemas.user_schema import (
    PadreRegisterRequest, 
    UserResponse, 
    Token, 
    LoginRequest
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

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Obtener el usuario actual desde el token"""
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
    user = await collection.find_one({"username": username})
    
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

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: PadreRegisterRequest):
    """Registrar un nuevo padre de familia"""
    db = get_database()
    collection = db["users"]
    
    # Check if user exists
    existing_user = await collection.find_one({
        "$or": [
            {"email": user_data.email}
        ]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario con este email ya existe"
        )
    
    # Create user document
    user_dict = user_data.model_dump(exclude={"password"})
    
    # Auto-generate username from email if not provided (Padres login with email usually, but system needs username)
    # We can use the part before @, but collisions.
    # We can just require username in schema OR effectively set username = email.
    # Let's set username = email to ensure uniqueness easily.
    user_dict["username"] = user_data.email
    
    user_dict["hashed_password"] = get_password_hash(user_data.password)
    user_dict["role"] = "PADRE"  # Asignar rol explícitamente
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    user_dict["is_active"] = True
    user_dict["is_superuser"] = False
    
    result = await collection.insert_one(user_dict)
    
    # Return created user
    user_dict["_id"] = str(result.inserted_id)
    return user_dict

from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login con username y password (compatible con Swagger UI)"""
    db = get_database()
    collection = db["users"]
    
    user = await collection.find_one({
        "$or": [
            {"username": form_data.username},
            {"email": form_data.username}
        ]
    })
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user
