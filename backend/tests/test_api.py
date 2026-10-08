import os
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_PUBLISHABLE_KEY", "test-publishable-key")
os.environ.setdefault("SUPABASE_SECRET_KEY", "test-server-secret")

import auth
import main


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.filters = {}
        self.operation = "select"
        self.payload = None
        self.single = False
        self.in_filters = {}

    def select(self, _columns):
        self.operation = "select"
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def in_(self, key, values):
        self.in_filters[key] = values
        return self

    def limit(self, _count):
        return self

    def order(self, _column, desc=False):
        return self

    def maybe_single(self):
        self.single = True
        return self

    def execute(self):
        if self.table_name == "profiles":
            return FakeResponse({"role": self.client.role})

        records = (
            self.client.resources
            if self.table_name == "resources"
            else self.client.incidents
        )
        matches = []
        for item in records:
            if not all(item.get(key) == value for key, value in self.filters.items()):
                continue
            if not all(item.get(key) in values for key, values in self.in_filters.items()):
                continue
            matches.append(item)
        if self.operation == "update":
            for item in matches:
                item.update(self.payload)
            return FakeResponse(matches)
        return FakeResponse(matches)


class FakeClient:
    def __init__(self, role="RESCUER", incidents=None, resources=None):
        self.role = role
        self.incidents = incidents or []
        self.resources = resources or []

    def table(self, table):
        return FakeQuery(self, table)


def _request_client(monkeypatch, role="RESCUER", incidents=None, resources=None):
    client = FakeClient(role, incidents, resources)
    monkeypatch.setattr(auth, "supabase", client)
    monkeypatch.setattr(auth, "supabase_admin", client)
    monkeypatch.setattr(main, "supabase", client)
    monkeypatch.setattr(main, "supabase_admin", client)
    user = SimpleNamespace(id="caller-1", email="caller@example.com")
    main.app.dependency_overrides[auth.get_current_user] = lambda: user
    return TestClient(main.app)


def test_status_workflow_rejects_jump_and_allows_next_step(monkeypatch):
    records = [{"id": 1, "user_id": "caller-1", "status": "NEW"}]
    client = _request_client(monkeypatch, incidents=records)
    try:
        jump = client.put(
            "/api/incidents/1/status",
            json={"status": "RESCUED"},
        )
        assert jump.status_code == 409
        assert records[0]["status"] == "NEW"

        next_step = client.put(
            "/api/incidents/1/status",
            json={"status": "ASSIGNED"},
        )
        assert next_step.status_code == 200
        assert next_step.json()["incident"]["status"] == "ASSIGNED"
    finally:
        main.app.dependency_overrides.clear()


def test_victim_cannot_update_incident_status(monkeypatch):
    client = _request_client(monkeypatch, role="VICTIM")
    try:
        response = client.put(
            "/api/incidents/1/status",
            json={"status": "ASSIGNED"},
        )
        assert response.status_code == 403
    finally:
        main.app.dependency_overrides.clear()


def test_victim_incident_list_is_owner_scoped(monkeypatch):
    records = [
        {"id": 1, "user_id": "caller-1", "status": "NEW"},
        {"id": 2, "user_id": "another-user", "status": "NEW"},
    ]
    client = _request_client(monkeypatch, role="VICTIM", incidents=records)
    try:
        response = client.get("/api/incidents")
        assert response.status_code == 200
        assert [item["id"] for item in response.json()["incidents"]] == [1]
    finally:
        main.app.dependency_overrides.clear()


def test_triage_endpoint_states_that_rules_are_not_ml(monkeypatch):
    records = [{
        "id": 1,
        "user_id": "caller-1",
        "status": "NEW",
        "message": "People are trapped and need help",
        "people_count": 2,
        "disaster_type": "FLOOD",
        "severity": None,
    }]
    client = _request_client(monkeypatch, incidents=records)
    try:
        response = client.put("/api/incidents/1/analyze")
        assert response.status_code == 200
        analysis = response.json()["analysis"]
        assert analysis["analysis_method"] == "rule_based_triage"
        assert analysis["machine_learning_used"] is False
        assert analysis["ai_confidence"] is None
        assert analysis["priority_reasons"]
    finally:
        main.app.dependency_overrides.clear()


def test_resource_recommendations_distinguish_recorded_availability(monkeypatch):
    resources = [
        {"id": 1, "type": "AMBULANCE", "available": True},
        {"id": 2, "type": "RESCUE_TEAM", "available": False},
    ]
    client = _request_client(
        monkeypatch,
        role="VICTIM",
        resources=resources,
    )
    try:
        response = client.post(
            "/api/resources/recommend",
            json={"disaster_type": "FLOOD", "severity": "CRITICAL"},
        )
        assert response.status_code == 200
        detail = {
            item["resource_type"]: item
            for item in response.json()["recommendation_details"]
        }
        assert detail["AMBULANCE"]["availability"] == "reported_available"
        assert detail["RESCUE_TEAM"]["availability"] == "recorded_unavailable"
        assert detail["MEDICAL_TEAM"]["availability"] == "no_inventory_recorded"
        assert "do not reserve" in response.json()["availability_note"]
    finally:
        main.app.dependency_overrides.clear()


def test_missing_bearer_token_is_rejected(monkeypatch):
    _request_client(monkeypatch)
    main.app.dependency_overrides.clear()
    try:
        response = TestClient(main.app).get("/api/incidents")
        assert response.status_code == 401
    finally:
        main.app.dependency_overrides.clear()
