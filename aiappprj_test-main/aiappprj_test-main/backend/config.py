from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Declare your variables with type annotations
    GEMINI_KEY: str

    # Tell Pydantic to read from the .env file
    model_config = SettingsConfigDict(env_file=".env")

# Instantiate to share across the application
settings = Settings()