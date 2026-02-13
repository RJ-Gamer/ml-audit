import uuid

import pytest

from ml_audit.models import (
    ModelVersion,
    PredictionEvent,
    Explanation,
    PredictionStatus,
)
from ml_audit.services import (
    ActorPayload,
    record_prediction_event,
    attach_explanation,
)


@pytest.mark.django_db
def test_attach_explanation_create_and_update():
    # Minimal model + prediction setup
    model = ModelVersion.objects.create(
        model_name="fraud_model",
        version="1.0.0",
    )

    prediction = PredictionEvent.objects.create(
        id=uuid.uuid4(),
        prediction_id="external-123",
        model=model,
        features={"amount": 100},
        output={"fraud_probability": 0.5},
        status=PredictionStatus.SUCCESS,
    )

    assert Explanation.objects.count() == 0

    # 1) Create explanation using PredictionEvent instance
    expl1 = attach_explanation(
        prediction=prediction,
        method="dummy_reason_codes",
        payload={"feature_importances": {"amount": 0.5}},
        summary_text="Amount contributed moderately.",
    )

    assert Explanation.objects.count() == 1
    assert expl1.prediction == prediction
    assert expl1.method == "dummy_reason_codes"
    assert expl1.payload["feature_importances"]["amount"] == 0.5
    assert "moderately" in expl1.summary_text

    # 2) Update explanation using UUID pk
    expl2 = attach_explanation(
        prediction=prediction.id,
        method="dummy_reason_codes",
        payload={"feature_importances": {"amount": 0.8}},
        summary_text="Amount contributed strongly.",
        status=PredictionStatus.PARTIAL,
        method_version="1.1",
    )

    assert Explanation.objects.count() == 1  # still one, updated in-place
    expl2.refresh_from_db()
    assert expl2.payload["feature_importances"]["amount"] == 0.8
    assert expl2.status == PredictionStatus.PARTIAL
    assert expl2.method_version == "1.1"
    assert "strongly" in expl2.summary_text

    # 3) Update explanation using external prediction_id string
    expl3 = attach_explanation(
        prediction="external-123",
        method="dummy_reason_codes",
        payload={"feature_importances": {"amount": 0.9}},
        summary_text="Amount contributed very strongly.",
    )

    assert Explanation.objects.count() == 1
    expl3.refresh_from_db()
    assert expl3.payload["feature_importances"]["amount"] == 0.9
    assert "very strongly" in expl3.summary_text

