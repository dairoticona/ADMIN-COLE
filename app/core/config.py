from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Admin Cole API"
    VERSION: str = "1.0.0"
    
    # MongoDB Configuration
    MONGODB_URL: str
    DATABASE_NAME: str = "admin_cole_db"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
