"""
Example DRF view showing how to use ml-audit in a prediction endpoint.
"""

from __future__ import annotations

from rest_framework import serializers, status, views
from rest_framework.response import Response

from ml_audit.services import (
    ActorPayload,
    attach_explanation,
    record_prediction_event,
)

# --- Dummy model for illustration only ---


class DummyFraudModel:
    def predict_proba(self, features: dict) -> float:
        # Replace with real model logic
        base = 0.1
        if features.get("amount", 0) > 1000:
            base += 0.4
        if features.get("is_new_customer"):
            base += 0.2
        return max(0.0, min(1.0, base))


model = DummyFraudModel()


# --- Request/response serializers ---


class FraudRequestSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    is_new_customer = serializers.BooleanField()
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)


class FraudResponseSerializer(serializers.Serializer):
    fraud_probability = serializers.FloatField()
    is_fraud = serializers.BooleanField()
    prediction_id = serializers.UUIDField()


# --- The view ---


class FraudPredictionView(views.APIView):
    """
    POST /fraud-predict/

    Example integration of ml-audit in a DRF endpoint.
    """

    def post(self, request, *args, **kwargs):
        serializer = FraudRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        features = serializer.validated_data

        # 1. Run the model
        score = model.predict_proba(features)
        is_fraud = score > 0.8
        output = {"fraud_probability": score, "is_fraud": is_fraud}

        # 2. Build actor payload from request (if authenticated)
        actor = None
        user = request.user if request.user and request.user.is_authenticated else None
        if user is not None:
            actor = ActorPayload(
                actor_type="user",
                actor_id=str(user.pk),
                tenant_id=getattr(user, "tenant_id", None),
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )

        # 3. Record prediction event
        prediction = record_prediction_event(
            model_name="dummy_fraud_model",
            model_version="1.0.0",
            features=features,
            output=output,
            decision_outcome="flagged" if is_fraud else "clean",
            confidence=score,
            actor=actor,
            environment="prod",
            trace_id=request.headers.get("X-Request-ID"),
        )

        # 4. (Optional) attach a simple explanation
        feature_importances = {
            "amount": 0.6 if features["amount"] > 1000 else 0.1,
            "is_new_customer": 0.3 if features["is_new_customer"] else 0.0,
        }
        attach_explanation(
            prediction=prediction,
            method="dummy_reason_codes",
            payload={"feature_importances": feature_importances},
            summary_text="High transaction amount and new customer status increased fraud risk.",
        )

        # 5. Build response
        response_data = FraudResponseSerializer(
            {
                "fraud_probability": score,
                "is_fraud": is_fraud,
                "prediction_id": prediction.id,
            }
        ).data
        return Response(response_data, status=status.HTTP_200_OK)
