from fastapi import APIRouter, HTTPException, UploadFile, File, status
from typing import List
from app.crud.crud_papa import papa as crud_papa
from app.schemas.papa_schema import PapaCreate, PapaUpdate, PapaResponse
from app.models.common import UserRole
from app.core.database import get_database
from app.core.security import get_password_hash
import openpyxl
from io import BytesIO
from bson import ObjectId

router = APIRouter()

@router.post("/import-padres", status_code=status.HTTP_201_CREATED)
async def import_padres(file: UploadFile = File(...)):
    """
    Importar padres masivamente desde Excel (Router Papas).
    Columnas: Email, Password, Nombre, Apellido, Telefono
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    contents = await file.read()
    workbook = openpyxl.load_workbook(BytesIO(contents))
    sheet = workbook.active

    db = get_database()
    creados = []
    errores = []

    for index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        try:
            # Asumimos orden: Email, Password, Nombre, Apellido, Telefono
            if not row[0] or not row[1]: 
                continue

            email = row[0]
            password = row[1]
            nombre = row[2]
            apellido = row[3]
            telefono = row[4]

            # Verificar si existe
            existing = await crud_papa.get_by_email(db, email=email)
            if existing:
                errores.append(f"Fila {index}: Email {email} ya existe")
                continue

            # Crear objeto PapaCreate
            user_in = PapaCreate(
                email=email,
                password=get_password_hash(str(password)),
                nombre=str(nombre) if nombre else "Sin Nombre",
                apellido=str(apellido) if apellido else "Sin Apellido",
                telefono=str(telefono) if telefono else None,
                role=UserRole.PADRE,
                hijos_ids=[] 
            )
            
            # create maneja el mapeo password -> hashed_password si se pasa plano
            # Aqui pasamos ya hasheado en password field. 
            # OJO: crud_papa.create espera password plano o lo que sea que venga en 'password' field y lo mueve a hashed_password.
            # Si pasamos hash en 'password', se guardará como 'hashed_password'. Correcto.
            
            nuevo_user = await crud_papa.create(db, obj_in=user_in)
            creados.append(nuevo_user)

        except Exception as e:
            errores.append(f"Fila {index}: Error - {str(e)}")

    return {
        "message": "Importación de padres finalizada",
        "creados_count": len(creados),
        "errores": errores
    }

@router.post("/bulk-delete-padres", status_code=status.HTTP_200_OK)
async def bulk_delete_padres(file: UploadFile = File(...)):
    """
    Eliminar padres masivamente basado en Email del Excel.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    contents = await file.read()
    workbook = openpyxl.load_workbook(BytesIO(contents))
    sheet = workbook.active

    db = get_database()
    collection = db["users"]
    eliminados = 0
    errores = []

    for index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        try:
            if not row[0]: # Email
                continue
            
            email = row[0]
            
            # Borrar por Email
            result = await collection.delete_one({"email": email})
            if result.deleted_count > 0:
                eliminados += 1
            else:
                errores.append(f"Fila {index}: Email {email} no encontrado")

        except Exception as e:
            errores.append(f"Fila {index}: Error - {str(e)}")

    return {
        "message": "Eliminación masiva de padres finalizada",
        "eliminados_count": eliminados,
        "errores": errores
    }

# --- Papas CRUD ---

@router.get("/", response_model=List[PapaResponse])
async def read_papas_list(skip: int = 0, limit: int = 100):
    """Listar todos los padres (Role = PADRE)"""
    db = get_database()
    collection = db["users"]
    cursor = collection.find({"role": UserRole.PADRE}).skip(skip).limit(limit).sort("created_at", -1)
    results = []
    async for doc in cursor:
        results.append(PapaResponse(**doc, id=doc["_id"]))
    return results

@router.post("/", response_model=PapaResponse, status_code=status.HTTP_201_CREATED)
async def create_papa(user_in: PapaCreate):
    """Crear un padre (Rol PADRE forzado)"""
    db = get_database()
    
    # Check email
    existing = await crud_papa.get_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    if user_in.password:
        user_in.password = get_password_hash(user_in.password)
    
    # Force Role
    user_in.role = UserRole.PADRE
    
    return await crud_papa.create(db, obj_in=user_in)

@router.get("/{id}", response_model=PapaResponse)
async def read_papa(id: str):
    """Obtener un padre por ID"""
    db = get_database()
    user = await crud_papa.get(db, id=id)
    # Check Role is PADRE? Yes
    # But user object returned is PapaModel.
    if not user or getattr(user, "role", None) != UserRole.PADRE:
        raise HTTPException(status_code=404, detail="Padre no encontrado")
    return user

@router.put("/{id}", response_model=PapaResponse)
async def update_papa(id: str, user_in: PapaUpdate):
    """Actualizar un padre"""
    db = get_database()
    user = await crud_papa.get(db, id=id)
    if not user or getattr(user, "role", None) != UserRole.PADRE:
        raise HTTPException(status_code=404, detail="Padre no encontrado")
    
    if user_in.password:
        user_in.password = get_password_hash(user_in.password)
        
    return await crud_papa.update(db, db_obj=user, obj_in=user_in)

@router.delete("/{id}", response_model=PapaResponse)
async def delete_papa(id: str):
    """Eliminar un padre"""
    db = get_database()
    user = await crud_papa.get(db, id=id)
    if not user or getattr(user, "role", None) != UserRole.PADRE:
        raise HTTPException(status_code=404, detail="Padre no encontrado")
    
    return await crud_papa.remove(db, id=id)
