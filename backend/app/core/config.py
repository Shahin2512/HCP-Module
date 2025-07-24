from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "HCP CRM Module"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str
    GROQ_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()