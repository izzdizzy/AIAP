from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Declare your variables with type annotations
    GEMINI_KEY: str
    
    # Diabetes module settings
    DIABETES_GEMINI_KEY: Optional[str] = None  # Can use same key or separate
    
    # Feature flags for modular control
    ENABLE_CAD: bool = True
    ENABLE_DIABETES: bool = True

    # Account system settings
    SECRET_KEY: str = "dev-insecure-secret-change-me"
    DATABASE_URL: str = "sqlite:///./app.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # Tell Pydantic to read from the .env file
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        extra='ignore'
    )

# Instantiate to share across the application
settings = Settings()