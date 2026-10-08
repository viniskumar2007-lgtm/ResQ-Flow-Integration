from services.ai_service import analyze_incident
from services.incident_workflow import can_transition_status
from services.priority_engine import calculate_priority
from services.resource_engine import recommend_resources


def test_triage_labels_heuristics_and_explains_priority():
    result = analyze_incident({
        "message": "Two people are trapped after the flood",
        "people_count": 2,
        "disaster_type": "FLOOD",
    })

    assert result["severity"] == "CRITICAL"
    assert result["analysis_method"] == "rule_based_triage"
    assert result["machine_learning_used"] is False
    assert result["ai_confidence"] is None
    assert result["priority_score"] == 90
    assert any("message keywords" in reason for reason in result["priority_reasons"])


def test_priority_score_is_bounded_and_people_factor_is_explained():
    result = calculate_priority("HIGH", 10000)

    assert result["priority_score"] == 80
    assert len(result["priority_reasons"]) == 2
    assert "10 additional points" in result["priority_reasons"][1]


def test_incident_workflow_only_allows_forward_transitions():
    assert can_transition_status("NEW", "ASSIGNED")
    assert can_transition_status("ASSIGNED", "RESCUE_IN_PROGRESS")
    assert can_transition_status("RESCUE_IN_PROGRESS", "RESCUED")
    assert not can_transition_status("NEW", "RESCUED")
    assert not can_transition_status("RESCUED", "ASSIGNED")


def test_resource_recommendations_normalize_inputs():
    assert recommend_resources(" flood ", "critical") == [
        "AMBULANCE",
        "RESCUE_TEAM",
        "MEDICAL_TEAM",
        "WATER",
    ]
