from pydantic_settings import BaseSettings
from typing import List
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
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str =  Field(..., env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int =  Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES")
    DEBUG: bool = Field(..., env="DEBUG")
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()



