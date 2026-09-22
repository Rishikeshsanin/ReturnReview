import pytest
from fastapi import HTTPException
from app.services.status_service import transition


def test_valid_transition():
    assert transition("DRAFT", "READY_FOR_INSPECTION") == "READY_FOR_INSPECTION"


def test_invalid_transition_is_rejected():
    with pytest.raises(HTTPException) as exc:
        transition("DRAFT", "APPROVED")
    assert exc.value.status_code == 409
