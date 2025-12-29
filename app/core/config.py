from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import Field
import os

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Admin Cole API"
    VERSION: str = "1.0.0"
    # MongoDB Configuration
    MONGODB_URL: str = Field(..., env="MONGODB_URL")
    DATABASE_NAME: str = Field("kyc_db", env="DATABASE_NAME")
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: Optional[str] = Field(None, env="CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: Optional[str] = Field(None, env="CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: Optional[str] = Field(None, env="CLOUDINARY_API_SECRET")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()



