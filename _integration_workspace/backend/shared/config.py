from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class SharedSettings(BaseSettings):
    """
    Merged environment variables from CAD and Readmission configurations.
    Includes fallback defaults for all settings.
    """
    
    # =========================================================================
    # GEMINI API KEYS
    # =========================================================================
    # Primary Gemini API key (CAD config - required with fallback)
    GEMINI_KEY: str = ""
    
    # Alternative name for Gemini API key (Readmission config - optional)
    GEMINI_API_KEY: Optional[str] = None
    
    # Diabetes module specific Gemini key (optional)
    DIABETES_GEMINI_KEY: Optional[str] = None
    
    # =========================================================================
    # FEATURE FLAGS
    # =========================================================================
    # Enable/disable CAD module
    ENABLE_CAD: bool = True
    
    # Enable/disable Diabetes module
    ENABLE_DIABETES: bool = True
    
    # Tell Pydantic to read from the .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Instantiate to share across the application
settings = SharedSettings()
