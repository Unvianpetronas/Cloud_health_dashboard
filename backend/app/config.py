from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

load_dotenv()

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AWS Cloud Health Dashboard"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000


    # YOUR AWS credentials (for your own infrastructure like DynamoDB)
    YOUR_AWS_REGION: str = "ap-southeast-1"
    YOUR_AWS_ACCESS_KEY_ID: Optional[str] = None
    YOUR_AWS_SECRET_ACCESS_KEY: Optional[str] = None


    DATABASE_URL: Optional[str] = None

    # DynamoDB Tables
    METRICS_TABLE: str = "CloudHealthMetrics"
    COSTS_TABLE: str = "CloudHealthCosts"
    SECURITY_TABLE: str = "SecurityFindings"
    RECOMMENDATIONS_TABLE: str = "Recommendations"

    # Redis (for caching)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Jwt_handler
    JWT_SECRET_KEY: Optional[str] = None
    ENCRYPTION_KEY: Optional[str] = None

    # Monitoring
    METRICS_COLLECTION_INTERVAL: int = 60  # seconds
    LOG_LEVEL: str = "INFO"

    # Cost Optimization
    COST_OPTIMIZATION_ENABLED: bool = True
    ML_MODEL_RETRAIN_INTERVAL: int = 86400  # 24 hours

    # DynamoDB Settings
    DYNAMODB_TABLE_PREFIX: str = "CloudHealth"
    METRICS_TTL_DAYS: int = 30
    COSTS_TTL_DAYS: int = 365

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'
        extra = "ignore"  # ADD THIS - ignores extra fields


settings = Settings()