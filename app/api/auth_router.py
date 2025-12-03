from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from typing import Annotated
from jose import jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer

from app.core.database import get_database
from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreate, UserResponse, Token, LoginRequest
from app.core.config import settings

router = APIRouter()

# Password handling
# Password handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    db = get_database()
    collection = db["users"]
    
    # Check if user exists
    existing_user = await collection.find_one({
        "$or": [
            {"email": user_data.email},
            {"username": user_data.username}
        ]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create user document
    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["hashed_password"] = get_password_hash(user_data.password)
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    user_dict["is_active"] = True
    user_dict["is_superuser"] = False
    
    result = await collection.insert_one(user_dict)
    
    # Return created user
    user_dict["_id"] = str(result.inserted_id)
    return user_dict

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Login and get access token"""
    db = get_database()
    collection = db["users"]
    
    user = await collection.find_one({"email": login_data.email})
    
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Obtener el usuario actual desde el token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = get_database()
    collection = db["users"]
    user = await collection.find_one({"email": email})
    
    if user is None:
        raise credentials_exception
    
    user["_id"] = str(user["_id"])
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user


# ========== CRUD DE USUARIOS ==========

@router.get("/", response_model=list[UserResponse])
async def get_all_users(skip: int = 0, limit: int = 100):
    """Obtener todos los usuarios"""
    db = get_database()
    collection = db["users"]
    
    users = []
    cursor = collection.find().skip(skip).limit(limit).sort("username", 1)
    
    async for user in cursor:
        user["_id"] = str(user["_id"])
        users.append(user)
    
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Obtener un usuario por ID"""
    from bson import ObjectId
    db = get_database()
    collection = db["users"]
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    user = await collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    user["_id"] = str(user["_id"])
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserCreate):
    """Actualizar un usuario"""
    from bson import ObjectId
    db = get_database()
    collection = db["users"]
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    # Verificar que el usuario existe
    existing_user = await collection.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Preparar datos para actualizar
    update_data = user_data.model_dump(exclude={"password"})
    update_data["hashed_password"] = get_password_hash(user_data.password)
    update_data["updated_at"] = datetime.utcnow()
    
    # Actualizar en la base de datos
    await collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # Obtener y retornar el usuario actualizado
    updated_user = await collection.find_one({"_id": ObjectId(user_id)})
    updated_user["_id"] = str(updated_user["_id"])
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """Eliminar un usuario"""
    from bson import ObjectId
    db = get_database()
    collection = db["users"]
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    # Verificar que el usuario existe
    existing_user = await collection.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Eliminar el usuario
    await collection.delete_one({"_id": ObjectId(user_id)})
    
    return None
