from typing import Any, Dict

from database import supabase_admin


# ============================================================
# Offline Incident Synchronization
# ============================================================

def sync_incident(
    incident_data: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Synchronize an offline incident with Supabase PostgreSQL.

    Flow:
        1. Validate local_id.
        2. Check whether the incident already exists.
        3. Create the incident if it does not exist.
        4. Return the synchronized incident.

    local_id provides idempotency and prevents duplicate
    incidents when an offline device retries synchronization.
    """

    # --------------------------------------------------------
    # Validate local ID
    # --------------------------------------------------------

    local_id = incident_data.get("local_id")

    if not local_id:
        raise ValueError(
            "local_id is required for synchronization"
        )

    # --------------------------------------------------------
    # Check for duplicate incident
    # --------------------------------------------------------

    existing_response = (
        supabase_admin
        .table("incidents")
        .select("*")
        .eq("local_id", local_id)
        .limit(1)
        .execute()
    )

    if existing_response.data:

        return {
            "success": True,
            "message": "Incident already synchronized",
            "duplicate": True,
            "incident": existing_response.data[0]
        }

    # --------------------------------------------------------
    # Prepare incident data
    # --------------------------------------------------------

    incident = {
        "user_id": user_id,
        "name": incident_data["name"],
        "message": incident_data["message"],
        "latitude": incident_data.get("latitude"),
        "longitude": incident_data.get("longitude"),
        "people_count": incident_data.get("people_count", 1),
        "disaster_type": incident_data.get("disaster_type"),
        "severity": incident_data.get("severity"),
        "local_id": local_id,
        "status": "NEW"
    }

    # --------------------------------------------------------
    # Preserve original offline timestamp
    # --------------------------------------------------------

    if incident_data.get("timestamp"):
        incident["timestamp"] = incident_data["timestamp"]

    # --------------------------------------------------------
    # Insert synchronized incident
    # --------------------------------------------------------

    response = (
        supabase_admin
        .table("incidents")
        .insert(incident)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Failed to synchronize incident"
        )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "success": True,
        "message": "Offline incident synchronized successfully",
        "duplicate": False,
        "incident": response.data[0]
    }