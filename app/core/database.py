from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        logger.info("Connecting to MongoDB...")
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.db = db.client[settings.DATABASE_NAME]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    try:
        logger.info("Closing MongoDB connection...")
        if db.client:
            db.client.close()
        logger.info("MongoDB connection closed!")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")

def get_database():
    """Get database instance"""
    return db.db

async def create_super_admin():
    """Create super admin user if not exists"""
    from app.models.user_model import UserRole
    from app.core.security import get_password_hash
    
    db_instance = get_database()
    collection = db_instance["users"]
    
    # Check if super admin exists
    admin_user = await collection.find_one({"username": "brandon"})
    
    if not admin_user:
        logger.info("Creating super admin user 'brandon'...")
        admin_data = {
            "email": "admin@admincole.com",
            "username": "brandon",
            "nombre": "Brandon",
            "apellido": "Lara",
            "role": UserRole.ADMIN,
            "hashed_password": get_password_hash("datahub12345"),
            "is_active": True,
            "is_superuser": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await collection.insert_one(admin_data)
        logger.info("Super admin user created successfully!")
    else:
        logger.info("Super admin user already exists.")
