from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, create_super_admin
from app.api.auth_router import router as auth_router
from app.api.admin_router import router as admin_router
from app.api.licencias_router import router as licencias_router
from app.api.cursos_router import router as cursos_router
from app.api.estudiantes_router import router as estudiantes_router
from app.api.eventos_router import router as eventos_router
from app.api.libretas_router import router as libretas_router
from app.api.mallas_router import router as mallas_router
from app.api.pagos_router import router as pagos_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Admin Cole API - Auth, Admin, Reuniones, Licencias & Hijos"
)

# CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los encabezados
)

# Event handlers
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    await create_super_admin()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(licencias_router, prefix="/api/licencias", tags=["licencias"])
app.include_router(cursos_router, prefix="/api/cursos", tags=["cursos"])
app.include_router(estudiantes_router, prefix="/api/estudiantes", tags=["estudiantes"])
app.include_router(eventos_router, prefix="/api/eventos", tags=["eventos"])
app.include_router(libretas_router, prefix="/api/libretas", tags=["libretas"])
app.include_router(mallas_router, prefix="/api/mallas", tags=["mallas"])
app.include_router(pagos_router, prefix="/api/pagos", tags=["pagos"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to Admin Cole API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
