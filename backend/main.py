import logging

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from auth import get_current_user, require_role
from database import supabase, supabase_admin

from schemas import (
    SOSCreate,
    IncidentStatusUpdate,
    ResourceCreate,
    ResourceRecommendationRequest,
    SyncSOSRequest,
    LoginRequest
)

from services.sync_service import sync_incident
from services.resource_engine import recommend_resources
from services.ai_service import analyze_incident as analyze_incident_with_rules
from services.incident_workflow import can_transition_status


logger = logging.getLogger(__name__)


# ============================================================
# Application Configuration
# ============================================================

app = FastAPI(
    title="ResQ-Flow API",
    description=(
        "Emergency Response and Rescue Coordination API "
        "for SOS management, incident analysis, "
        "resource coordination and offline synchronization."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================================
# CORS Configuration
# ============================================================
# Common development frontend ports:
# 5500 -> VS Code Live Server
# 5173 -> Vite
# 3000 -> React/other development servers

ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",

    "http://localhost:5173",
    "http://127.0.0.1:5173",

    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=[
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "OPTIONS"
    ],
    allow_headers=["Authorization", "Content-Type"],
)


# ============================================================
# Constants
# ============================================================

ALLOWED_INCIDENT_STATUSES = {
    "NEW",
    "ASSIGNED",
    "RESCUE_IN_PROGRESS",
    "RESCUED"
}

ALLOWED_ROLES = {"VICTIM", "RESCUER", "ADMIN"}


ALLOWED_RESOURCE_TYPES = {
    "AMBULANCE",
    "RESCUE_TEAM",
    "MEDICAL_TEAM",
    "SHELTER",
    "FOOD",
    "WATER"
}


@app.get("/api/me")
def get_current_profile(current_user=Depends(get_current_user)):
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
        },
        "role": get_user_role(current_user.id),
    }


# ============================================================
# Helper Functions
# ============================================================

def get_user_role(user_id: str) -> str:
    """
    Retrieve the role of an authenticated user.
    """

    try:
        response = (
            supabase_admin
            .table("profiles")
            .select("role")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=403,
                detail="User profile not found"
            )

        role = response.data["role"]
        if role not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=403,
                detail="User profile has an unsupported role"
            )
        return role

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("User-role lookup failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to verify user role"
        )


# ============================================================
# Root & Health
# ============================================================

@app.get("/")
def root():
    """
    Basic API information.
    """

    return {
        "success": True,
        "message": "ResQ-Flow API is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """
    Health check endpoint.
    """

    return {
        "success": True,
        "status": "healthy"
    }


# ============================================================
# Authentication
# ============================================================

@app.post("/api/auth/login")
def login(login_data: LoginRequest):
    """
    Authenticate a user using Supabase Auth.
    """

    try:
        response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })

        if response.user is None or response.session is None:
            raise HTTPException(
                status_code=401,
                detail="Login failed"
            )

        return {
            "success": True,
            "message": "Login successful",
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.warning("Supabase login failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


# ============================================================
# SOS
# ============================================================

@app.post("/api/sos")
def create_sos(
    sos: SOSCreate,
    current_user=Depends(get_current_user)
):
    """
    Create a new emergency SOS incident.
    """

    try:
        if sos.local_id:
            result = sync_incident(
                incident_data=sos.model_dump(mode="json"),
                user_id=current_user.id,
            )
            result["message"] = (
                "SOS already synchronized"
                if result["duplicate"]
                else "SOS created successfully"
            )
            return result

        incident_data = {
            "user_id": current_user.id,
            "name": sos.name,
            "message": sos.message,
            "latitude": sos.latitude,
            "longitude": sos.longitude,
            "people_count": sos.people_count,
            "disaster_type": sos.disaster_type,
            "severity": sos.severity,
            "status": "NEW"
        }

        response = (
            supabase_admin
            .table("incidents")
            .insert(incident_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create SOS"
            )

        return {
            "success": True,
            "message": "SOS created successfully",
            "incident": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("SOS creation failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to create SOS"
        )


# ============================================================
# INCIDENTS
# ============================================================

@app.get("/api/incidents")
def get_incidents(
    current_user=Depends(get_current_user)
):
    """
    Retrieve incidents based on the user's role.

    RESCUER / ADMIN:
        Can view all incidents.

    VICTIM:
        Can view only their own incidents.
    """

    try:
        user_role = get_user_role(current_user.id)

        if user_role in {"RESCUER", "ADMIN"}:

            response = (
                supabase_admin
                .table("incidents")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )

        elif user_role == "VICTIM":

            response = (
                supabase_admin
                .table("incidents")
                .select("*")
                .eq("user_id", current_user.id)
                .order("created_at", desc=True)
                .execute()
            )
        else:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view incidents"
            )

        return {
            "success": True,
            "count": len(response.data),
            "incidents": response.data
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Incident list lookup failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch incidents"
        )


@app.get("/api/incidents/{incident_id}")
def get_incident(
    incident_id: int,
    current_user=Depends(get_current_user)
):
    """
    Retrieve a specific incident.

    RESCUER / ADMIN:
        Can view any incident.

    VICTIM:
        Can view only their own incident.
    """

    try:
        user_role = get_user_role(current_user.id)

        response = (
            supabase_admin
            .table("incidents")
            .select("*")
            .eq("id", incident_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        incident = response.data[0]

        if user_role in {"RESCUER", "ADMIN"}:
            return {
                "success": True,
                "incident": incident
            }

        if incident["user_id"] != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view this incident"
            )

        return {
            "success": True,
            "incident": incident
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Incident lookup failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch incident"
        )


# ============================================================
# INCIDENT STATUS
# ============================================================

@app.put("/api/incidents/{incident_id}/status")
def update_incident_status(
    incident_id: int,
    status_update: IncidentStatusUpdate,
    current_user=Depends(
        require_role("RESCUER", "ADMIN")
    )
):
    """
    Update the status of an emergency incident.
    """

    if status_update.status not in ALLOWED_INCIDENT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid incident status"
        )

    try:
        current_response = (
            supabase_admin
            .table("incidents")
            .select("id,status")
            .eq("id", incident_id)
            .limit(1)
            .execute()
        )

        if not current_response.data:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        current_status = current_response.data[0].get("status")
        if not can_transition_status(current_status, status_update.status):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot transition incident from {current_status} to {status_update.status}"
            )

        response = (
            supabase_admin
            .table("incidents")
            .update({
                "status": status_update.status
            })
            .eq("id", incident_id)
            .eq("status", current_status)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=409,
                detail="Incident status changed; refresh and retry"
            )

        return {
            "success": True,
            "message": "Incident status updated successfully",
            "incident": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Incident status update failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to update incident status"
        )


# ============================================================
# INCIDENT ANALYSIS
# ============================================================

@app.put("/api/incidents/{incident_id}/analyze")
def analyze_incident(
    incident_id: int,
    current_user=Depends(
        require_role("RESCUER", "ADMIN")
    )
):
    """
    Produce an explainable rule-based triage result.
    """

    try:
        incident_response = (
            supabase_admin
            .table("incidents")
            .select("*")
            .eq("id", incident_id)
            .limit(1)
            .execute()
        )
        if not incident_response.data:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        triage = analyze_incident_with_rules(incident_response.data[0])
        response = (
            supabase_admin
            .table("incidents")
            .update(triage)
            .eq("id", incident_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        return {
            "success": True,
            "message": "Rule-based triage completed; no ML model was used",
            "incident": response.data[0],
            "analysis": triage,
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Incident triage failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to update incident analysis"
        )


# ============================================================
# RESOURCES
# ============================================================

@app.get("/api/resources")
def get_resources(
    current_user=Depends(get_current_user)
):
    """
    Retrieve available emergency resources.
    """

    try:
        response = (
            supabase_admin
            .table("resources")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "success": True,
            "count": len(response.data),
            "resources": response.data,
            "availability_note": (
                "Availability is manually reported and may be stale."
            ),
        }

    except Exception as exc:
        logger.error("Resource lookup failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch resources"
        )


@app.post("/api/resources")
def create_resource(
    resource: ResourceCreate,
    current_user=Depends(
        require_role("RESCUER", "ADMIN")
    )
):
    """
    Create a new emergency resource.
    """

    if resource.type not in ALLOWED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid resource type"
        )

    try:
        resource_data = {
            "name": resource.name,
            "type": resource.type,
            "latitude": resource.latitude,
            "longitude": resource.longitude,
            "available": resource.available,
            "contact": resource.contact
        }

        response = (
            supabase_admin
            .table("resources")
            .insert(resource_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create resource"
            )

        return {
            "success": True,
            "message": "Resource created successfully",
            "resource": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Resource creation failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to create resource"
        )


@app.put("/api/resources/{resource_id}")
def update_resource(
    resource_id: int,
    resource: ResourceCreate,
    current_user=Depends(
        require_role("RESCUER", "ADMIN")
    )
):
    """
    Update an existing emergency resource.
    """

    if resource.type not in ALLOWED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid resource type"
        )

    try:
        existing_response = (
            supabase_admin
            .table("resources")
            .select("id")
            .eq("id", resource_id)
            .execute()
        )

        if not existing_response.data:
            raise HTTPException(
                status_code=404,
                detail="Resource not found"
            )

        resource_data = {
            "name": resource.name,
            "type": resource.type,
            "latitude": resource.latitude,
            "longitude": resource.longitude,
            "available": resource.available,
            "contact": resource.contact
        }

        response = (
            supabase_admin
            .table("resources")
            .update(resource_data)
            .eq("id", resource_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to update resource"
            )

        return {
            "success": True,
            "message": "Resource updated successfully",
            "resource": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Resource update failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to update resource"
        )


# ============================================================
# RESOURCE RECOMMENDATION
# ============================================================

@app.post("/api/resources/recommend")
def recommend_incident_resources(
    request: ResourceRecommendationRequest,
    current_user=Depends(get_current_user)
):
    """
    Recommend resources based on disaster type and severity.
    """

    try:
        recommended_types = recommend_resources(
            request.disaster_type,
            request.severity
        )
        inventory_response = (
            supabase_admin
            .table("resources")
            .select("*")
            .in_("type", recommended_types)
            .execute()
        )
        inventory = inventory_response.data or []
        details = []
        for resource_type in recommended_types:
            matching = [
                resource
                for resource in inventory
                if resource.get("type") == resource_type
            ]
            available = [
                resource for resource in matching
                if resource.get("available") is True
            ]
            details.append({
                "resource_type": resource_type,
                "available_count": len(available),
                "available_resources": available,
                "availability": (
                    "reported_available"
                    if available
                    else "recorded_unavailable"
                    if matching
                    else "no_inventory_recorded"
                ),
            })

        return {
            "success": True,
            "recommendations": recommended_types,
            "recommendation_details": details,
            "availability_note": (
                "Availability reflects recorded inventory only; "
                "recommendations do not reserve or dispatch resources."
            ),
        }

    except Exception as exc:
        logger.error("Resource recommendation failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to generate resource recommendations"
        )


# ============================================================
# OFFLINE SYNCHRONIZATION
# ============================================================

@app.post("/api/sync")
def sync_offline_sos(
    sos: SyncSOSRequest,
    current_user=Depends(get_current_user)
):
    """
    Synchronize an offline SOS with PostgreSQL.

    Duplicate protection is handled using local_id.
    """

    try:
        incident_data = sos.model_dump(mode="json")

        result = sync_incident(
            incident_data=incident_data,
            user_id=current_user.id
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as exc:
        logger.error("Offline SOS synchronization failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Failed to synchronize incident"
        )