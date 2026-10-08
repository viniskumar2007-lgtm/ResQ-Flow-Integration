from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ============================================================
# Common Constants
# ============================================================

ALLOWED_SEVERITIES = {
    "LOW",
    "MODERATE",
    "HIGH",
    "CRITICAL"
}

ALLOWED_STATUSES = {
    "NEW",
    "ASSIGNED",
    "RESCUE_IN_PROGRESS",
    "RESCUED"
}

ALLOWED_RESOURCE_TYPES = {
    "AMBULANCE",
    "RESCUE_TEAM",
    "MEDICAL_TEAM",
    "SHELTER",
    "FOOD",
    "WATER"
}


# ============================================================
# SOS
# ============================================================

class SOSCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    message: str = Field(
        ...,
        min_length=5,
        max_length=2000
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180
    )

    people_count: int = Field(
        default=1,
        ge=1,
        le=10000
    )

    disaster_type: Optional[str] = Field(
        default=None,
        max_length=50
    )

    severity: Optional[str] = Field(
        default=None,
        max_length=20
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value):
        if value is None:
            return value

        value = value.upper()

        if value not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Invalid severity. Allowed values: "
                f"{', '.join(sorted(ALLOWED_SEVERITIES))}"
            )

        return value


# ============================================================
# Incident Status
# ============================================================

class IncidentStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        value = value.upper()

        if value not in ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid incident status. Allowed values: "
                f"{', '.join(sorted(ALLOWED_STATUSES))}"
            )

        return value


# ============================================================
# Resource
# ============================================================

class ResourceCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    type: str

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180
    )

    available: bool = True

    contact: Optional[str] = Field(
        default=None,
        max_length=20
    )

    @field_validator("type")
    @classmethod
    def validate_resource_type(cls, value):
        value = value.upper()

        if value not in ALLOWED_RESOURCE_TYPES:
            raise ValueError(
                f"Invalid resource type. Allowed values: "
                f"{', '.join(sorted(ALLOWED_RESOURCE_TYPES))}"
            )

        return value


# ============================================================
# Incident Analysis
# ============================================================

class IncidentAnalysis(BaseModel):
    disaster_type: Optional[str] = Field(
        default=None,
        max_length=50
    )

    severity: Optional[str] = Field(
        default=None,
        max_length=20
    )

    priority_score: int = Field(
        default=0,
        ge=0,
        le=100
    )

    ai_confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1
    )

    @field_validator("severity")
    @classmethod
    def validate_analysis_severity(cls, value):
        if value is None:
            return value

        value = value.upper()

        if value not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Invalid severity. Allowed values: "
                f"{', '.join(sorted(ALLOWED_SEVERITIES))}"
            )

        return value


# ============================================================
# Resource Recommendation
# ============================================================

class ResourceRecommendationRequest(BaseModel):
    disaster_type: Optional[str] = Field(
        default=None,
        max_length=50
    )

    severity: Optional[str] = Field(
        default=None,
        max_length=20
    )

    @field_validator("severity")
    @classmethod
    def validate_recommendation_severity(cls, value):
        if value is None:
            return value

        value = value.upper()

        if value not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Invalid severity. Allowed values: "
                f"{', '.join(sorted(ALLOWED_SEVERITIES))}"
            )

        return value


# ============================================================
# Offline Synchronization
# ============================================================

class SyncSOSRequest(BaseModel):
    local_id: str = Field(
        ...,
        min_length=1,
        max_length=150
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    message: str = Field(
        ...,
        min_length=5,
        max_length=2000
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180
    )

    people_count: int = Field(
        default=1,
        ge=1,
        le=10000
    )

    disaster_type: Optional[str] = Field(
        default=None,
        max_length=50
    )

    severity: Optional[str] = Field(
        default=None,
        max_length=20
    )

    timestamp: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_sync_severity(cls, value):
        if value is None:
            return value

        value = value.upper()

        if value not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Invalid severity. Allowed values: "
                f"{', '.join(sorted(ALLOWED_SEVERITIES))}"
            )

        return value


# ============================================================
# Authentication
# ============================================================

class LoginRequest(BaseModel):
    email: str = Field(
        ...,
        min_length=5,
        max_length=255
    )

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )