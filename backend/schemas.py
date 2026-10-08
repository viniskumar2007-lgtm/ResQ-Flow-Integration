from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


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
    local_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150
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

    @field_validator("name", "message")
    @classmethod
    def trim_required_text(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("local_id")
    @classmethod
    def trim_local_id(cls, value):
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("local_id cannot be blank")
        return value

    @field_validator("disaster_type")
    @classmethod
    def normalize_disaster_type(cls, value):
        return value.strip().upper() if value else value

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value):
        if value is None:
            return value

        value = value.strip().upper()

        if value not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Invalid severity. Allowed values: "
                f"{', '.join(sorted(ALLOWED_SEVERITIES))}"
            )

        return value

    @model_validator(mode="after")
    def validate_coordinate_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


# ============================================================
# Incident Status
# ============================================================

class IncidentStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        value = value.strip().upper()

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

    available: bool

    contact: Optional[str] = Field(
        default=None,
        max_length=20
    )

    @field_validator("type")
    @classmethod
    def validate_resource_type(cls, value):
        value = value.strip().upper()

        if value not in ALLOWED_RESOURCE_TYPES:
            raise ValueError(
                f"Invalid resource type. Allowed values: "
                f"{', '.join(sorted(ALLOWED_RESOURCE_TYPES))}"
            )

        return value

    @field_validator("name")
    @classmethod
    def trim_resource_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("name cannot be blank")
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

        value = value.strip().upper()

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

        value = value.strip().upper()

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

    timestamp: Optional[datetime] = None

    @field_validator("local_id", "name", "message")
    @classmethod
    def trim_required_text(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("disaster_type")
    @classmethod
    def normalize_disaster_type(cls, value):
        return value.strip().upper() if value else value

    @field_validator("severity")
    @classmethod
    def validate_sync_severity(cls, value):
        if value is None:
            return value

        value = value.strip().upper()

        if value not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Invalid severity. Allowed values: "
                f"{', '.join(sorted(ALLOWED_SEVERITIES))}"
            )

        return value

    @model_validator(mode="after")
    def validate_coordinate_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


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

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value):
        value = value.strip()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("A valid email address is required")
        return value