"""
Application Settings and Configuration
Uses environment variables with sensible defaults
"""

import os
from pathlib import Path
from typing import Optional, List
from functools import lru_cache


class Settings:
    """
    Application configuration class
    Loads settings from environment variables with defaults
    """

    # ==========================================================================
    # PROJECT PATHS
    # ==========================================================================
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    SRC_DIR: Path = PROJECT_ROOT / "src"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

    # ==========================================================================
    # APPLICATION SETTINGS
    # ==========================================================================
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_NAME: str = os.getenv("APP_NAME", "MediSafeAI")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")

    # ==========================================================================
    # LOGGING CONFIGURATION
    # ==========================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE: str = os.getenv("LOG_FILE", str(LOGS_DIR / "app.log"))
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # ==========================================================================
    # DATABASE CONFIGURATION
    # ==========================================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://medisafe_user:medisafe_password@localhost:5432/medisafe_db"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"

    # Airflow database
    AIRFLOW_DATABASE_URL: str = os.getenv(
        "AIRFLOW_DATABASE_URL",
        "postgresql://airflow_user:airflow_password@localhost:5432/airflow_db"
    )

    # ==========================================================================
    # DIFFERENTIAL PRIVACY SETTINGS
    # ==========================================================================
    DEFAULT_EPSILON: float = float(os.getenv("DEFAULT_EPSILON", "1.0"))
    DEFAULT_DELTA: float = float(os.getenv("DEFAULT_DELTA", "1e-5"))
    MAX_EPSILON: float = float(os.getenv("MAX_EPSILON", "10.0"))
    PRIVACY_MECHANISM: str = os.getenv("PRIVACY_MECHANISM", "auto")

    # ==========================================================================
    # DATA GENERATION SETTINGS
    # ==========================================================================
    DEFAULT_NUM_PATIENTS: int = int(os.getenv("DEFAULT_NUM_PATIENTS", "1000"))
    RANDOM_SEED: Optional[int] = (
        int(os.getenv("RANDOM_SEED"))
        if os.getenv("RANDOM_SEED") and os.getenv("RANDOM_SEED") != "None"
        else None
    )

    # Data directories
    DATA_OUTPUT_DIR: Path = Path(os.getenv("DATA_OUTPUT_DIR", str(DATA_DIR / "raw")))
    DATA_PROCESSED_DIR: Path = Path(os.getenv("DATA_PROCESSED_DIR", str(DATA_DIR / "processed")))
    DATA_PRIVATE_DIR: Path = Path(os.getenv("DATA_PRIVATE_DIR", str(DATA_DIR / "private")))

    # ==========================================================================
    # FLASK API CONFIGURATION
    # ==========================================================================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "5000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "4"))
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "300"))
    API_MAX_REQUESTS: int = int(os.getenv("API_MAX_REQUESTS", "1000"))
    API_MAX_REQUESTS_JITTER: int = int(os.getenv("API_MAX_REQUESTS_JITTER", "50"))

    # CORS
    CORS_ENABLED: bool = os.getenv("CORS_ENABLED", "True").lower() == "true"
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # API Authentication
    API_KEY_ENABLED: bool = os.getenv("API_KEY_ENABLED", "False").lower() == "true"
    API_KEY: Optional[str] = os.getenv("API_KEY")

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "2592000"))  # 30 days

    # ==========================================================================
    # AIRFLOW CONFIGURATION
    # ==========================================================================
    AIRFLOW_HOME: str = os.getenv("AIRFLOW_HOME", "/opt/airflow")
    AIRFLOW_WEBSERVER_PORT: int = int(os.getenv("AIRFLOW_WEBSERVER_PORT", "8080"))
    AIRFLOW_EXECUTOR: str = os.getenv("AIRFLOW_EXECUTOR", "LocalExecutor")
    AIRFLOW_LOAD_EXAMPLES: bool = os.getenv("AIRFLOW_LOAD_EXAMPLES", "False").lower() == "true"
    AIRFLOW_DAGS_FOLDER: str = os.getenv("AIRFLOW_DAGS_FOLDER", "/opt/airflow/dags")

    # ==========================================================================
    # REDIS CONFIGURATION
    # ==========================================================================
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://:{REDIS_PASSWORD or ''}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

    # Cache settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"

    # ==========================================================================
    # CELERY CONFIGURATION
    # ==========================================================================
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_TASK_SERIALIZER: str = os.getenv("CELERY_TASK_SERIALIZER", "json")
    CELERY_RESULT_SERIALIZER: str = os.getenv("CELERY_RESULT_SERIALIZER", "json")
    CELERY_ACCEPT_CONTENT: List[str] = [os.getenv("CELERY_ACCEPT_CONTENT", "json")]
    CELERY_TIMEZONE: str = os.getenv("CELERY_TIMEZONE", "UTC")
    CELERY_ENABLE_UTC: bool = os.getenv("CELERY_ENABLE_UTC", "True").lower() == "true"

    # ==========================================================================
    # SPARK CONFIGURATION
    # ==========================================================================
    SPARK_MASTER: str = os.getenv("SPARK_MASTER", "local[*]")
    SPARK_APP_NAME: str = os.getenv("SPARK_APP_NAME", "MediSafeAI")
    SPARK_DRIVER_MEMORY: str = os.getenv("SPARK_DRIVER_MEMORY", "2g")
    SPARK_EXECUTOR_MEMORY: str = os.getenv("SPARK_EXECUTOR_MEMORY", "4g")
    SPARK_EXECUTOR_CORES: int = int(os.getenv("SPARK_EXECUTOR_CORES", "2"))

    # ==========================================================================
    # MONITORING & OBSERVABILITY
    # ==========================================================================
    OTEL_ENABLED: bool = os.getenv("OTEL_ENABLED", "False").lower() == "true"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4317"
    )
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "medisafe-ai")
    OTEL_TRACES_SAMPLER: str = os.getenv("OTEL_TRACES_SAMPLER", "always_on")

    # Prometheus
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "False").lower() == "true"
    PROMETHEUS_PORT: int = int(os.getenv("PROMETHEUS_PORT", "9090"))

    # ==========================================================================
    # SECURITY SETTINGS
    # ==========================================================================
    HIPAA_MODE_ENABLED: bool = os.getenv("HIPAA_MODE_ENABLED", "True").lower() == "true"
    DATA_ENCRYPTION_ENABLED: bool = os.getenv("DATA_ENCRYPTION_ENABLED", "True").lower() == "true"
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "change-this-encryption-key-32chars")

    # Audit logging
    AUDIT_LOG_ENABLED: bool = os.getenv("AUDIT_LOG_ENABLED", "True").lower() == "true"
    AUDIT_LOG_FILE: str = os.getenv("AUDIT_LOG_FILE", str(LOGS_DIR / "audit.log"))

    # ==========================================================================
    # DISEASE SIMULATION PARAMETERS
    # ==========================================================================
    DISEASE_PROGRESSION_ENABLED: bool = os.getenv(
        "DISEASE_PROGRESSION_ENABLED",
        "True"
    ).lower() == "true"
    DEFAULT_NUM_VISITS: int = int(os.getenv("DEFAULT_NUM_VISITS", "12"))
    DEFAULT_TIME_INTERVAL_DAYS: int = int(os.getenv("DEFAULT_TIME_INTERVAL_DAYS", "30"))

    # Intervention simulation
    INTERVENTION_FREQUENCY_DAYS: int = int(os.getenv("INTERVENTION_FREQUENCY_DAYS", "90"))
    INTERVENTION_EFFECT_MIN: float = float(os.getenv("INTERVENTION_EFFECT_MIN", "0.05"))
    INTERVENTION_EFFECT_MAX: float = float(os.getenv("INTERVENTION_EFFECT_MAX", "0.15"))

    # ==========================================================================
    # TEMPORAL PATTERNS CONFIGURATION
    # ==========================================================================
    ANOMALY_PROBABILITY: float = float(os.getenv("ANOMALY_PROBABILITY", "0.05"))
    ANOMALY_MULTIPLIER_MIN: float = float(os.getenv("ANOMALY_MULTIPLIER_MIN", "1.5"))
    ANOMALY_MULTIPLIER_MAX: float = float(os.getenv("ANOMALY_MULTIPLIER_MAX", "2.5"))

    # Seasonal patterns
    SEASONAL_AMPLITUDE: float = float(os.getenv("SEASONAL_AMPLITUDE", "0.1"))
    SEASONAL_PERIOD_DAYS: int = int(os.getenv("SEASONAL_PERIOD_DAYS", "365"))

    # ==========================================================================
    # EMAIL NOTIFICATIONS
    # ==========================================================================
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@medisafe.ai")
    SMTP_STARTTLS: bool = os.getenv("SMTP_STARTTLS", "True").lower() == "true"
    SMTP_SSL: bool = os.getenv("SMTP_SSL", "False").lower() == "true"

    # ==========================================================================
    # AWS CONFIGURATION
    # ==========================================================================
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")
    S3_ENABLED: bool = os.getenv("S3_ENABLED", "False").lower() == "true"

    # ==========================================================================
    # TESTING CONFIGURATION
    # ==========================================================================
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://test_user:test_password@localhost:5432/test_medisafe"
    )
    TEST_DATA_DIR: Path = Path(os.getenv("TEST_DATA_DIR", str(PROJECT_ROOT / "tests" / "test_data")))
    PYTEST_WORKERS: str = os.getenv("PYTEST_WORKERS", "auto")

    # ==========================================================================
    # DEVELOPMENT SETTINGS
    # ==========================================================================
    JUPYTER_PORT: int = int(os.getenv("JUPYTER_PORT", "8888"))
    JUPYTER_TOKEN: str = os.getenv("JUPYTER_TOKEN", "medisafe-dev-token")
    HOT_RELOAD: bool = os.getenv("HOT_RELOAD", "True").lower() == "true"
    DEBUG_TOOLBAR_ENABLED: bool = os.getenv("DEBUG_TOOLBAR_ENABLED", "True").lower() == "true"

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.APP_ENV.lower() == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.APP_ENV.lower() == "development"

    @classmethod
    def is_testing(cls) -> bool:
        """Check if running in testing environment"""
        return cls.APP_ENV.lower() == "testing"

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_DIR,
            cls.DATA_OUTPUT_DIR,
            cls.DATA_PROCESSED_DIR,
            cls.DATA_PRIVATE_DIR,
            cls.LOGS_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_database_url(cls, for_testing: bool = False) -> str:
        """Get appropriate database URL"""
        if for_testing or cls.is_testing():
            return cls.TEST_DATABASE_URL
        return cls.DATABASE_URL

    @classmethod
    def validate_config(cls):
        """Validate critical configuration settings"""
        errors = []

        # Check production requirements
        if cls.is_production():
            if cls.SECRET_KEY == "change-this-secret-key-in-production":
                errors.append("SECRET_KEY must be changed in production")
            if cls.ENCRYPTION_KEY == "change-this-encryption-key-32chars":
                errors.append("ENCRYPTION_KEY must be changed in production")

        # Validate privacy settings
        if cls.DEFAULT_EPSILON <= 0:
            errors.append("DEFAULT_EPSILON must be positive")
        if cls.DEFAULT_DELTA <= 0:
            errors.append("DEFAULT_DELTA must be positive")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors))

    def __repr__(self):
        return f"<Settings env={self.APP_ENV} debug={self.DEBUG}>"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Use this function to get settings throughout the application
    """
    settings = Settings()
    settings.ensure_directories()
    if not settings.is_development():
        settings.validate_config()
    return settings


# Global settings instance
settings = get_settings()
