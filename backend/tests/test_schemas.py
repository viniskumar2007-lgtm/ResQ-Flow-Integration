import pytest
from pydantic import ValidationError

from schemas import ResourceCreate, SOSCreate, SyncSOSRequest


def test_sos_rejects_unpaired_coordinates():
    with pytest.raises(ValidationError):
        SOSCreate(
            name="Caller",
            message="Need urgent help",
            latitude=12.5,
        )


def test_sync_request_normalizes_values_and_validates_timestamp():
    request = SyncSOSRequest(
        local_id=" device:1 ",
        name=" Caller ",
        message=" Help needed ",
        latitude=12.5,
        longitude=77.5,
        severity=" high ",
        timestamp="2026-10-08T10:00:00Z",
    )

    assert request.local_id == "device:1"
    assert request.name == "Caller"
    assert request.severity == "HIGH"
    assert request.timestamp is not None


def test_resource_availability_must_be_explicit():
    with pytest.raises(ValidationError):
        ResourceCreate(name="Team", type="RESCUE_TEAM")
