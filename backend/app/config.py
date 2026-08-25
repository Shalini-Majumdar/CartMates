from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(..., description="Database connection URL")
    secret_key: str = Field(..., description="Secret key for JWT authentication")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    class Config:
        env_file = ".env"


settings = Settings()