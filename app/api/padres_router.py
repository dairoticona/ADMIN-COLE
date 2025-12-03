from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from typing import List, Annotated
from jose import jwt, JWTError
import bcrypt
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId

from app.core.database import get_database
from app.models.padre_model import PadreModel
from app.schemas.padre_schema import (
    PadreCreate, 
    PadreUpdate, 
    PadreResponse, 
    PadreToken, 
    PadreLoginRequest
)
from app.core.config import settings

router = APIRouter()

# OAuth2 scheme para padres
oauth2_scheme_padres = OAuth2PasswordBearer(tokenUrl="/api/padres/login")

# Password handling
def get_password_hash(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password, hashed_password):
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_padre(token: Annotated[str, Depends(oauth2_scheme_padres)]):
    """Obtener el padre actual desde el token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = get_database()
    collection = db["padres"]
    padre = await collection.find_one({"email": email})
    
    if padre is None:
        raise credentials_exception
    
    padre["_id"] = str(padre["_id"])
    return padre


# ========== AUTENTICACIÓN ==========

@router.post("/register", response_model=PadreResponse, status_code=status.HTTP_201_CREATED)
async def register_padre(padre_data: PadreCreate):
    """Registrar un nuevo padre"""
    db = get_database()
    collection = db["padres"]
    
    # Verificar si el padre ya existe
    existing_padre = await collection.find_one({
        "$or": [
            {"email": padre_data.email},
            {"username": padre_data.username}
        ]
    })
    
    if existing_padre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un padre con este email o username"
        )
    
    # Crear documento de padre
    padre_dict = padre_data.model_dump(exclude={"password"})
    padre_dict["hashed_password"] = get_password_hash(padre_data.password)
    padre_dict["created_at"] = datetime.utcnow()
    padre_dict["updated_at"] = datetime.utcnow()
    padre_dict["is_active"] = True
    
    result = await collection.insert_one(padre_dict)
    
    # Retornar padre creado
    padre_dict["_id"] = str(result.inserted_id)
    return padre_dict


@router.post("/login", response_model=PadreToken)
async def login_padre(login_data: PadreLoginRequest):
    """Login de padre y obtener token de acceso"""
    db = get_database()
    collection = db["padres"]
    
    padre = await collection.find_one({"email": login_data.email})
    
    if not padre or not verify_password(login_data.password, padre["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not padre.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta inactiva"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": padre["email"], "type": "padre"}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=PadreResponse)
async def get_current_padre_info(current_padre: Annotated[dict, Depends(get_current_padre)]):
    """Obtener información del padre actual"""
    return current_padre


# ========== CRUD DE PADRES ==========

@router.get("/", response_model=List[PadreResponse])
async def get_all_padres(skip: int = 0, limit: int = 100):
    """Obtener todos los padres"""
    db = get_database()
    collection = db["padres"]
    
    padres = []
    cursor = collection.find().skip(skip).limit(limit).sort("username", 1)
    
    async for padre in cursor:
        padre["_id"] = str(padre["_id"])
        padres.append(padre)
    
    return padres


@router.get("/{padre_id}", response_model=PadreResponse)
async def get_padre(padre_id: str):
    """Obtener un padre por ID"""
    db = get_database()
    collection = db["padres"]
    
    if not ObjectId.is_valid(padre_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de padre inválido"
        )
    
    padre = await collection.find_one({"_id": ObjectId(padre_id)})
    
    if not padre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Padre no encontrado"
        )
    
    padre["_id"] = str(padre["_id"])
    return padre


@router.put("/{padre_id}", response_model=PadreResponse)
async def update_padre(padre_id: str, padre_data: PadreUpdate):
    """Actualizar un padre"""
    db = get_database()
    collection = db["padres"]
    
    if not ObjectId.is_valid(padre_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de padre inválido"
        )
    
    # Verificar que el padre existe
    existing_padre = await collection.find_one({"_id": ObjectId(padre_id)})
    if not existing_padre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Padre no encontrado"
        )
    
    # Preparar datos para actualizar
    update_data = padre_data.model_dump(exclude_unset=True)
    
    if update_data:
        # Si se actualiza la contraseña, hashearla
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Actualizar en la base de datos
        await collection.update_one(
            {"_id": ObjectId(padre_id)},
            {"$set": update_data}
        )
    
    # Obtener y retornar el padre actualizado
    updated_padre = await collection.find_one({"_id": ObjectId(padre_id)})
    updated_padre["_id"] = str(updated_padre["_id"])
    return updated_padre


@router.delete("/{padre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_padre(padre_id: str):
    """Eliminar un padre"""
    db = get_database()
    collection = db["padres"]
    
    if not ObjectId.is_valid(padre_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de padre inválido"
        )
    
    # Verificar que el padre existe
    existing_padre = await collection.find_one({"_id": ObjectId(padre_id)})
    if not existing_padre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Padre no encontrado"
        )
    
    # Eliminar el padre
    await collection.delete_one({"_id": ObjectId(padre_id)})
    
    return None

