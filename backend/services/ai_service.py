from services.priority_engine import calculate_priority


SEVERITY_ORDER = ("LOW", "MODERATE", "HIGH", "CRITICAL")
CRITICAL_TERMS = ("trapped", "life-threatening", "immediate danger")
HIGH_TERMS = ("injured", "injury", "missing", "fire", "collapse")


def analyze_incident(incident):
    """Apply transparent triage rules; no machine-learning model is used."""
    message = (incident.get("message") or "").lower()
    try:
        people_count = max(1, int(incident.get("people_count") or 1))
    except (TypeError, ValueError):
        people_count = 1
    supplied_severity = incident.get("severity")

    if supplied_severity:
        severity = (
            supplied_severity.strip().upper()
            if isinstance(supplied_severity, str)
            else "LOW"
        )
        severity_source = "reported severity"
        if severity not in SEVERITY_ORDER:
            severity = "LOW"
            severity_source = "invalid severity fallback"
    elif any(term in message for term in CRITICAL_TERMS):
        severity = "CRITICAL"
        severity_source = "message keywords"
    elif any(term in message for term in HIGH_TERMS) or people_count >= 10:
        severity = "HIGH"
        severity_source = "message keywords or affected-person count"
    elif people_count >= 3:
        severity = "MODERATE"
        severity_source = "affected-person count"
    else:
        severity = "LOW"
        severity_source = "default when no higher-risk signal is supplied"

    priority = calculate_priority(severity, people_count)
    reasons = [f"Severity is {severity} based on {severity_source}."]
    reasons.extend(priority["priority_reasons"])

    return {
        "disaster_type": incident.get("disaster_type"),
        "severity": severity,
        "priority_score": priority["priority_score"],
        "priority_reasons": reasons,
        "analysis_method": "rule_based_triage",
        "machine_learning_used": False,
        "ai_confidence": None,
    }