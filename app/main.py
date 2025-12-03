from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, create_super_admin
from app.api.auth_router import router as auth_router
from app.api.admin_router import router as admin_router
from app.api.reuniones_router import router as reuniones_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Admin Cole API - Auth, Admin & Reuniones"
)

# CORS middleware
if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
app.include_router(reuniones_router, prefix="/api/reuniones", tags=["reuniones"])

@app.get("/")
async def root():
    return {"message": "Welcome to Admin Cole API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
