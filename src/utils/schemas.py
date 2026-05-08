"""
Data Validation Schemas using Pydantic
Provides validation for API requests, data generation, and privacy operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator


# =============================================================================
# ENUMS
# =============================================================================

class GenderEnum(str, Enum):
    """Patient gender options"""
    MALE = "M"
    FEMALE = "F"


class InsuranceTypeEnum(str, Enum):
    """Insurance type options"""
    PRIVATE = "Private"
    MEDICARE = "Medicare"
    MEDICAID = "Medicaid"
    UNINSURED = "Uninsured"


class PrivacyMechanismEnum(str, Enum):
    """Differential privacy mechanism options"""
    LAPLACE = "laplace"
    GAUSSIAN = "gaussian"
    AUTO = "auto"


class ExportFormatEnum(str, Enum):
    """Data export format options"""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    EXCEL = "excel"


# =============================================================================
# PATIENT SCHEMAS
# =============================================================================

class PatientBase(BaseModel):
    """Base patient schema"""
    patient_id: str = Field(..., description="Unique patient identifier")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    gender: GenderEnum
    dob: date = Field(..., description="Date of birth")
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    zip_code: str = Field(..., regex=r'^\d{5}$', description="5-digit zip code")
    income: float = Field(..., ge=0, description="Annual income in USD")
    insurance: InsuranceTypeEnum
    diabetes: bool = Field(default=False)
    hypertension: bool = Field(default=False)
    heart_disease: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "PT000001",
                "first_name": "John",
                "last_name": "Doe",
                "gender": "M",
                "dob": "1985-06-15",
                "age": 39,
                "zip_code": "12345",
                "income": 75000.0,
                "insurance": "Private",
                "diabetes": False,
                "hypertension": False,
                "heart_disease": False
            }
        }


class PatientCreate(BaseModel):
    """Schema for creating patients"""
    num_patients: int = Field(default=1000, ge=1, le=1000000, description="Number of patients to generate")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")

    class Config:
        json_schema_extra = {
            "example": {
                "num_patients": 1000,
                "seed": 42
            }
        }


class PatientResponse(PatientBase):
    """Schema for patient response"""
    created_at: Optional[datetime] = None


# =============================================================================
# VITALS SCHEMAS
# =============================================================================

class VitalsBase(BaseModel):
    """Base vitals schema"""
    patient_id: str
    blood_pressure_systolic: float = Field(..., ge=60, le=250, description="Systolic BP in mmHg")
    blood_pressure_diastolic: float = Field(..., ge=40, le=150, description="Diastolic BP in mmHg")
    heart_rate: float = Field(..., ge=30, le=200, description="Heart rate in bpm")
    blood_glucose: float = Field(..., ge=50, le=500, description="Blood glucose in mg/dL")
    cholesterol: float = Field(..., ge=100, le=400, description="Total cholesterol in mg/dL")
    body_temperature: float = Field(..., ge=95, le=105, description="Body temperature in °F")
    respiratory_rate: float = Field(..., ge=8, le=40, description="Respiratory rate in breaths/min")
    oxygen_saturation: float = Field(..., ge=70, le=100, description="Oxygen saturation in %")
    weight: float = Field(..., ge=50, le=500, description="Weight in lbs")

    @validator('blood_pressure_systolic', 'blood_pressure_diastolic')
    def validate_blood_pressure(cls, v, values):
        """Ensure systolic > diastolic"""
        if 'blood_pressure_diastolic' in values and 'blood_pressure_systolic' in values:
            if values.get('blood_pressure_systolic', 0) <= values.get('blood_pressure_diastolic', 0):
                raise ValueError('Systolic blood pressure must be greater than diastolic')
        return v


class VitalsCreate(BaseModel):
    """Schema for generating vitals"""
    patient_ids: Optional[List[str]] = Field(default=None, description="List of patient IDs")
    include_all_patients: bool = Field(default=True, description="Generate vitals for all patients")


# =============================================================================
# DISEASE PROGRESSION SCHEMAS
# =============================================================================

class DiseaseProgressionRequest(BaseModel):
    """Schema for disease progression simulation"""
    patient_id: str = Field(..., description="Patient ID for simulation")
    num_visits: int = Field(default=12, ge=1, le=100, description="Number of visits to simulate")
    time_interval_days: int = Field(default=30, ge=1, le=365, description="Days between visits")
    include_interventions: bool = Field(default=True, description="Include intervention effects")

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "PT000001",
                "num_visits": 12,
                "time_interval_days": 30,
                "include_interventions": True
            }
        }


# =============================================================================
# DIFFERENTIAL PRIVACY SCHEMAS
# =============================================================================

class PrivacyConfig(BaseModel):
    """Differential privacy configuration"""
    epsilon: float = Field(default=1.0, gt=0, le=20, description="Privacy budget (epsilon)")
    delta: float = Field(default=1e-5, gt=0, lt=1, description="Privacy violation probability")
    mechanism: PrivacyMechanismEnum = Field(default=PrivacyMechanismEnum.AUTO, description="Privacy mechanism")

    @validator('epsilon')
    def validate_epsilon(cls, v):
        """Warn about low privacy budgets"""
        if v > 10.0:
            # This would typically log a warning
            pass
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "epsilon": 1.0,
                "delta": 1e-5,
                "mechanism": "auto"
            }
        }


class PrivacyRequest(BaseModel):
    """Schema for applying differential privacy"""
    input_file: str = Field(..., description="Path to input data file")
    output_file: Optional[str] = Field(default=None, description="Path to output file")
    privacy_config: PrivacyConfig = Field(default_factory=PrivacyConfig)
    numeric_columns: List[str] = Field(..., description="Columns to apply numeric privacy")
    categorical_columns: Optional[List[str]] = Field(default=[], description="Columns to apply categorical privacy")

    class Config:
        json_schema_extra = {
            "example": {
                "input_file": "data/raw/patients.csv",
                "output_file": "data/private/patients_private.csv",
                "privacy_config": {
                    "epsilon": 1.0,
                    "delta": 1e-5,
                    "mechanism": "auto"
                },
                "numeric_columns": ["age", "income"],
                "categorical_columns": ["insurance"]
            }
        }


class PrivacyStatisticsRequest(BaseModel):
    """Schema for computing private statistics"""
    data: List[float] = Field(..., description="Numeric data for statistics")
    privacy_config: PrivacyConfig = Field(default_factory=PrivacyConfig)
    statistics: List[str] = Field(default=["mean", "variance"], description="Statistics to compute")

    @validator('statistics')
    def validate_statistics(cls, v):
        """Validate requested statistics"""
        allowed_stats = ["mean", "variance", "std", "median", "count"]
        for stat in v:
            if stat not in allowed_stats:
                raise ValueError(f"Statistic '{stat}' not allowed. Choose from: {allowed_stats}")
        return v


# =============================================================================
# API RESPONSE SCHEMAS
# =============================================================================

class APIResponse(BaseModel):
    """Generic API response"""
    status: str = Field(..., description="Response status (success/error)")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
                "data": {"records_generated": 1000},
                "timestamp": "2025-01-15T12:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema"""
    status: str = Field(default="error")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy")
    version: str
    uptime_seconds: float
    database_connected: bool
    redis_connected: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# DATA EXPORT SCHEMAS
# =============================================================================

class ExportRequest(BaseModel):
    """Schema for data export requests"""
    input_file: str = Field(..., description="Path to input data file")
    output_file: str = Field(..., description="Path to output file")
    export_format: ExportFormatEnum = Field(..., description="Export format")
    columns: Optional[List[str]] = Field(default=None, description="Columns to export (None = all)")
    apply_privacy: bool = Field(default=False, description="Apply differential privacy before export")
    privacy_config: Optional[PrivacyConfig] = Field(default=None, description="Privacy configuration if apply_privacy=True")

    @root_validator
    def validate_privacy_config(cls, values):
        """Ensure privacy_config is provided when apply_privacy=True"""
        if values.get('apply_privacy') and not values.get('privacy_config'):
            values['privacy_config'] = PrivacyConfig()
        return values


# =============================================================================
# TEMPORAL PATTERNS SCHEMAS
# =============================================================================

class TemporalPatternRequest(BaseModel):
    """Schema for adding temporal patterns"""
    input_file: str = Field(..., description="Path to input data file")
    column: str = Field(..., description="Column to apply pattern")
    pattern_type: str = Field(..., description="Pattern type: trend, anomaly, seasonal")
    parameters: Dict[str, Any] = Field(..., description="Pattern-specific parameters")

    @validator('pattern_type')
    def validate_pattern_type(cls, v):
        """Validate pattern type"""
        allowed_patterns = ["trend", "anomaly", "seasonal"]
        if v not in allowed_patterns:
            raise ValueError(f"Pattern type must be one of: {allowed_patterns}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "input_file": "data/raw/vitals.csv",
                "column": "blood_glucose",
                "pattern_type": "trend",
                "parameters": {
                    "trend_slope": 0.05,
                    "noise_level": 0.1
                }
            }
        }


# =============================================================================
# MACHINE LEARNING SCHEMAS
# =============================================================================

class MLModelTypeEnum(str, Enum):
    """ML Model types"""
    DISEASE_PREDICTOR = "disease_predictor"
    VITALS_FORECASTER = "vitals_forecaster"


class MLTrainRequest(BaseModel):
    """Schema for model training requests"""
    model_type: MLModelTypeEnum
    target_column: str = Field(..., description="Column to predict")
    feature_columns: List[str] = Field(..., description="Columns to use as features")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    random_state: int = Field(default=42)

    class Config:
        json_schema_extra = {
            "example": {
                "model_type": "disease_predictor",
                "target_column": "diabetes",
                "feature_columns": ["age", "blood_pressure_systolic", "blood_glucose", "weight"],
                "test_size": 0.2
            }
        }


class MLPredictRequest(BaseModel):
    """Schema for prediction requests"""
    model_type: MLModelTypeEnum
    features: Dict[str, Any] = Field(..., description="Feature values for prediction")


class MLPredictionResponse(BaseModel):
    """Schema for prediction responses"""
    model_type: str
    prediction: Any
    probability: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# BATCH OPERATION SCHEMAS
# =============================================================================

class BatchGenerationRequest(BaseModel):
    """Schema for batch data generation"""
    num_patients: int = Field(default=1000, ge=1, le=1000000)
    include_vitals: bool = Field(default=True)
    include_progression: bool = Field(default=False)
    include_treatments: bool = Field(default=True)
    apply_privacy: bool = Field(default=False)
    privacy_config: Optional[PrivacyConfig] = Field(default=None)
    output_directory: str = Field(default="data/raw")
    seed: Optional[int] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "num_patients": 5000,
                "include_vitals": True,
                "include_progression": False,
                "include_treatments": True,
                "apply_privacy": True,
                "privacy_config": {
                    "epsilon": 1.0,
                    "delta": 1e-5
                },
                "output_directory": "data/raw",
                "seed": 42
            }
        }
