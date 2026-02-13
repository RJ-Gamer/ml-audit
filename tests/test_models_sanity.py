# tests/test_models_sanity.py

import uuid

import pytest
from django.utils import timezone

from ml_audit.models import (
    ActorTypeChoice,
    Explanation,
    FrameworkChoice,
    ModelVersion,
    PredictionEvent,
    PredictionStatus,
    RequestingActor,
)


@pytest.mark.django_db
def test_can_create_basic_prediction_with_explanation():
    model = ModelVersion.objects.create(
        model_name="credit_risk_score",
        version="1.0.0",
        framework=FrameworkChoice.SKLEARN,
    )

    actor = RequestingActor.objects.create(
        actor_type=ActorTypeChoice.USER,
        actor_id="user-123",
        tenant_id="tenant-abc",
    )

    prediction_id = str(uuid.uuid4())

    prediction = PredictionEvent.objects.create(
        prediction_id=prediction_id,
        timestamp=timezone.now(),
        model=model,
        actor=actor,
        environment="prod",
        features={"age": 42, "income": 100000},
        output={"score": 0.87},
        confidence=0.87,
        decision_outcome="approved",
        status=PredictionStatus.SUCCESS,
    )

    explanation = Explanation.objects.create(
        prediction=prediction,
        method="shap",
        payload={"age": 0.3, "income": 0.7},
        summary_text="Income contributed more to the approval than age.",
    )

    assert prediction.prediction_id == prediction_id
    assert explanation.prediction == prediction
    assert explanation.method == "shap"
    assert explanation.status == PredictionStatus.SUCCESS
