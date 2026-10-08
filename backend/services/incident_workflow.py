ALLOWED_STATUS_TRANSITIONS = {
    "NEW": {"ASSIGNED"},
    "ASSIGNED": {"RESCUE_IN_PROGRESS"},
    "RESCUE_IN_PROGRESS": {"RESCUED"},
    "RESCUED": set(),
}


def can_transition_status(current_status, next_status):
    return next_status in ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
