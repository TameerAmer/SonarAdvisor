import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    app_name: str = "SonarQube AI Advisor"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database settings
    database_url: str = "sqlite:///./sonar_advisor.db"
    
    # JWT settings
    secret_key: str = "Tameer!Secret?Key.For-Sonar@Advisor"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120  # Extended to 2 hours
    
    # SonarQube settings
    sonarqube_url: str = "http://localhost:9000"
    sonarqube_token: Optional[str] = None
    sonarqube_username: Optional[str] = None
    sonarqube_password: Optional[str] = None
    
    # AI settings
    ai_model_type: str = "openai"  # Options: "rule_based", "openai", "local_llm"
    openai_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()