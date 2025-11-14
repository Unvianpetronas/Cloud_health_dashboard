from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from cryptography.fernet import Fernet


environment = os.getenv("ENVIRONMENT", "production")
env_file = f".env.{environment}"
if os.path.exists(env_file):
    load_dotenv(env_file)
load_dotenv()  # Load .env as fallback


class BaseConfig(BaseSettings):
    """Base configuration with common settings"""

    # Application
    APP_NAME: str = "AWS Cloud Health Dashboard"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = environment

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # AWS Configuration (for your infrastructure)
    YOUR_AWS_REGION: str = "ap-southeast-1"
    YOUR_AWS_ACCESS_KEY_ID: Optional[str] = None
    YOUR_AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Database
    DATABASE_URL: Optional[str] = None

    # DynamoDB Tables
    DYNAMODB_TABLE_PREFIX: str = "CloudHealth"
    CLIENTS_TABLE: str = "CloudHealthClients"
    METRICS_TABLE: str = "CloudHealthMetrics"
    COSTS_TABLE: str = "CloudHealthCosts"
    SECURITY_TABLE: str = "SecurityFindings"
    RECOMMENDATIONS_TABLE: str = "Recommendations"

    # SES
    SES_SENDER_EMAIL: str = "noreply@cloudhealthdashboard.xyz"
    FRONTEND_URL: str = "https://cloudhealthdashboard.xyz"
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    #Secrets Manager
    USE_SECRETS_MANAGER: bool = True  # Enabled with async support - no event loop blocking

    #Security Monitoring
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    ENABLE_SECURITY_ALERTS: bool = True

    #CloudWatch Monitoring
    CLOUDWATCH_NAMESPACE: str = "CloudHealth"
    ENABLE_DETAILED_MONITORING: bool = True

    # Multi-Tenant Settings
    MAX_CLIENTS_PER_INSTANCE: int = 50
    WORKER_COLLECTION_INTERVAL: int = 600  # 10 minutes
    WORKER_COLLECTION_STAGGER_SECONDS: int = 10  # Delay between clients

    # Business Logic
    METRICS_COLLECTION_INTERVAL: int = 60
    COST_OPTIMIZATION_ENABLED: bool = True
    ML_MODEL_RETRAIN_INTERVAL: int = 86400
    METRICS_TTL_DAYS: int = 30
    COSTS_TTL_DAYS: int = 365

    class Config:
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = "ignore"


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    # Auto-generate secure keys for development
    @property
    def JWT_SECRET_KEY(self) -> str:
        env_key = os.getenv("JWT_SECRET_KEY")
        if env_key:
            return env_key
        return "dev-jwt-secret-key-must-be-32-chars-minimum-for-security"

    @property
    def ENCRYPTION_KEY(self) -> str:
        env_key = os.getenv("ENCRYPTION_KEY")
        if env_key:
            return env_key
        # Fixed dev key for consistent development
        return "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg="


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = [
        "https://cloudhealthdashboard.xyz",
        "https://www.cloudhealthdashboard.xyz",
        "http://cloudhealthdashboard.xyz",
        "http://www.cloudhealthdashboard.xyz"
    ] # Must be set via environment

    # Production requires real secrets from environm0ent
    JWT_SECRET_KEY: str
    ENCRYPTION_KEY: str

    # Production-specific settings
    HTTPS_ONLY: bool = True
    SECURE_COOKIES: bool = True


def get_settings() -> BaseConfig:
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()


def validate_settings(settings: BaseConfig):
    errors = []

    if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
        errors.append("JWT_SECRET_KEY must be at least 32 characters")

    if not settings.ENCRYPTION_KEY:
        errors.append("ENCRYPTION_KEY is required")
    else:
        try:
            Fernet(settings.ENCRYPTION_KEY.encode())
        except Exception:
            errors.append("ENCRYPTION_KEY is not a valid Fernet key")
#
#    if settings.ENVIRONMENT == "production":
 #       if settings.DEBUG:
  #          errors.append("DEBUG must be False in production")
   #     if not settings.CORS_ORIGINS:
    #        errors.append("CORS_ORIGINS must be set in production")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


settings = get_settings()
validate_settings(settings)