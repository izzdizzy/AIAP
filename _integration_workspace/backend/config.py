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

    # Tell Pydantic to read from the .env file
    model_config = SettingsConfigDict(env_file=".env")

# Instantiate to share across the application
settings = Settings()