from functools import wraps
from typing import Any, Callable, Dict, Optional, Union
from time import perf_counter
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request

try:
    from rest_framework.response import Response
    from rest_framework import status
    from rest_framework.request import Request
except ImportError:  # pragma: no cover
    raise ImportError(
        "djangorestframework is required for ml_audit.integrations.drf. "
        "Install with `pip install django-ml-audit[drf]`."
    )


from ml_audit.models import PredictionEvent, PredictionStatus
from ml_audit.services import ActorPayload, attach_explanation, record_prediction_event


def audited_prediction(
    model_name: str,
    model_version: str,
    environment: str = "prod",
    decision_field: Optional[str] = None,
    confidence_field: Optional[str] = None,
    explanation_builder: Optional[Callable] = None,
    decision_outcome_field: Optional[str] = None,
) -> Callable:
    """
    Decorator for DRF views that automatically records prediction events.

    Usage:

    @audited_prediction(
        model_name="fraud_model",
        model_version="1.0.0",
        decision_field="is_fraud",
        confidence_field="fraud_probability",
    )
    def predict_fraud(features: dict, request: Request) -> dict:
        # Your model logic here
        return {"fraud_probability": 0.75, "is_fraud": True}
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(self, request: Request, *args: Any, **kwargs: Any) -> Response:
            features = getattr(request, "validated_data", request.data)

            actor = None
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                actor = ActorPayload(
                    actor_type="user",
                    actor_id=str(user.id),
                    tenant_id=getattr(user, "tenant_id", None),
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.META.get("HTTP_USER_AGENT"),
                )

            start = perf_counter()

            try:
                output = view_func(self, request, *args, **kwargs)
                status_code = PredictionStatus.SUCCESS
            except Exception:
                latency = (perf_counter() - start) * 1000

                record_prediction_event(
                    model_name=model_name,
                    model_version=model_version,
                    environment=environment,
                    features=features,
                    status=PredictionStatus.FAILED,
                    actor=actor,
                    output={"error": "exception"},
                    trace_id=request.headers.get("X-Request-ID"),
                    latency_ms=latency,
                )

                raise  # Preserve original API behavior

            latency = (perf_counter() - start) * 1000

            decision = output.get(decision_field) if decision_field else None
            confidence = output.get(confidence_field) if confidence_field else None
            decision_outcome = (
                output.get(decision_outcome_field) if decision_outcome_field else None
            )

            prediction_event = record_prediction_event(
                model_name=model_name,
                model_version=model_version,
                environment=environment,
                features=features,
                confidence=confidence,
                decision_outcome=decision_outcome,
                status=status_code,
                actor=actor,
                output=output,
                trace_id=request.headers.get("X-Request-ID"),
                latency_ms=latency,
            )

            if explanation_builder and status_code == PredictionStatus.SUCCESS:
                explanation_data = explanation_builder(
                    features, output, prediction_event
                )

                attach_explanation(
                    prediction=prediction_event,
                    method="auto",
                    payload=explanation_data["payload"],
                    summary_text=explanation_data["summary"],
                )

            response_data = {**output, "prediction_id": prediction_event.prediction_id}

            return Response(response_data, status=status.HTTP_200_OK)
        return wrapper
    return decorator