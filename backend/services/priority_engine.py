SEVERITY_BASE_SCORES = {
    "LOW": 20,
    "MODERATE": 45,
    "HIGH": 70,
    "CRITICAL": 90,
}


def calculate_priority(severity, people_count=1):
    """Return a deterministic score and the factors used to calculate it."""
    normalized_severity = (severity or "LOW").strip().upper()
    if normalized_severity not in SEVERITY_BASE_SCORES:
        normalized_severity = "LOW"

    try:
        people = max(1, int(people_count or 1))
    except (TypeError, ValueError):
        people = 1

    base_score = SEVERITY_BASE_SCORES[normalized_severity]
    people_bonus = min(10, (people - 1) // 2)
    score = min(100, base_score + people_bonus)
    reasons = [
        f"{normalized_severity} severity contributes {base_score} points.",
    ]
    if people_bonus:
        reasons.append(
            f"{people} people reported contributes {people_bonus} additional points."
        )
    else:
        reasons.append("No additional people-count points were added.")

    return {
        "priority_score": score,
        "priority_reasons": reasons,
    }