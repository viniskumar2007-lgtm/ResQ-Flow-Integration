from typing import Optional
from pydantic import BaseModel


# ============================================================
# Incident Model
# ============================================================

class IncidentModel(BaseModel):
    id: Optional[int] = None
    user_id: Optional[str] = None

    name: str
    message: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    timestamp: Optional[str] = None

    people_count: int = 1

    disaster_type: Optional[str] = None
    severity: Optional[str] = None

    priority_score: Optional[int] = None

    status: str = "NEW"

    ai_confidence: Optional[float] = None

    local_id: Optional[str] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ============================================================
# Resource Model
# ============================================================

class ResourceModel(BaseModel):
    id: Optional[int] = None

    name: str
    type: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    available: bool = True

    contact: Optional[str] = None

    created_at: Optional[str] = None