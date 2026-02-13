# tests/test_record_prediction_event.py

import uuid

import pytest

from ml_audit.models import (
    ModelVersion,
    RequestingActor,
    PredictionEvent,
)
from ml_audit.services import (
    ActorPayload,
    record_prediction_event,
)


@pytest.mark.django_db
def test_record_prediction_event_creates_related_objects_and_redacts_email(settings):
    # Configure redaction for the test
    settings.ML_AUDIT_REDACTION = {
        "ALLOWLIST": ["amount"],
        "DENYLIST": [],
        "MASK_VALUE": "[redacted]",
    }

    actor_payload = ActorPayload(
        actor_type="user",
        actor_id="user-123",
        tenant_id="tenant-xyz",
        ip_address="127.0.0.1",
        user_agent="pytest-agent",
    )

    features = {
        "amount": 1500,
        "email": "user@example.com",
    }

    output = {
        "fraud_probability": 0.91,
        "is_fraud": True,
    }

    prediction = record_prediction_event(
        model_name="fraud_model",
        model_version="1.0.0",
        features=features,
        output=output,
        decision_outcome="flagged",
        confidence=0.91,
        actor=actor_payload,
        environment="test",
        trace_id=str(uuid.uuid4()),
    )

    # Reload from DB
    prediction_db = PredictionEvent.objects.select_related("model", "actor").get(
        pk=prediction.pk
    )

    # ModelVersion created and linked
    assert prediction_db.model.model_name == "fraud_model"
    assert prediction_db.model.version == "1.0.0"
    assert ModelVersion.objects.count() == 1

    # RequestingActor created and linked
    assert prediction_db.actor is not None
    assert prediction_db.actor.actor_type == "user"
    assert prediction_db.actor.actor_id == "user-123"
    assert prediction_db.actor.tenant_id == "tenant-xyz"
    assert RequestingActor.objects.count() == 1

    # Features redacted correctly: amount kept, email masked
    assert prediction_db.features["amount"] == 1500
    assert prediction_db.features["email"] == "[redacted]"

    # Output & metadata stored correctly
    assert prediction_db.output["fraud_probability"] == 0.91
    assert prediction_db.output["is_fraud"] is True
    assert prediction_db.decision_outcome == "flagged"
    assert prediction_db.environment == "test"
