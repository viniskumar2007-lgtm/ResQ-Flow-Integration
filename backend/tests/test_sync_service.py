import sys
import types


database_stub = types.ModuleType("database")
database_stub.supabase_admin = None
sys.modules.setdefault("database", database_stub)

from services import sync_service


class Response:
    def __init__(self, data):
        self.data = data


class DuplicateError(Exception):
    code = "23505"


class FakeTable:
    def __init__(self, database, name):
        self.database = database
        self.name = name
        self.filters = {}
        self.operation = None
        self.payload = None

    def select(self, _columns):
        self.operation = "select"
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def limit(self, _count):
        return self

    def execute(self):
        if self.operation == "select":
            key = (
                self.filters.get("user_id"),
                self.filters.get("local_id"),
            )
            record = self.database.records.get(key)
            if self.database.simulate_race and not self.database.race_observed:
                self.database.race_observed = True
                return Response([])
            return Response([record] if record else [])

        key = (
            self.payload["user_id"],
            self.payload["local_id"],
        )
        if key in self.database.records:
            raise DuplicateError()
        self.database.records[key] = self.payload
        if self.database.simulate_race:
            raise DuplicateError()
        return Response([self.payload])


class FakeDatabase:
    def __init__(self, simulate_race=False):
        self.records = {}
        self.simulate_race = simulate_race
        self.race_observed = False

    def table(self, name):
        assert name == "incidents"
        return FakeTable(self, name)


def test_sync_is_idempotent_and_scoped_to_authenticated_user(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr(sync_service, "supabase_admin", database)
    incident = {
        "local_id": "offline-1",
        "name": "Caller",
        "message": "Need urgent help",
    }

    first = sync_service.sync_incident(incident, "user-a")
    retry = sync_service.sync_incident(incident, "user-a")
    other_user = sync_service.sync_incident(incident, "user-b")

    assert first["duplicate"] is False
    assert retry["duplicate"] is True
    assert other_user["duplicate"] is False
    assert len(database.records) == 2


def test_sync_recovers_from_unique_conflict_race(monkeypatch):
    database = FakeDatabase(simulate_race=True)
    monkeypatch.setattr(sync_service, "supabase_admin", database)

    result = sync_service.sync_incident(
        {
            "local_id": "offline-race",
            "name": "Caller",
            "message": "Need urgent help",
        },
        "user-a",
    )

    assert result["duplicate"] is True
