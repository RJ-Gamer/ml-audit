"""
Example DRF view showing how to use ml-audit in a prediction endpoint.
"""

from __future__ import annotations

from rest_framework import serializers, views

from ml_audit.integrations.drf import audited_prediction

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


def build_fraud_explanation(features, output, prediction):
    features_importances = {
        "amount": 0.6 if features["amount"] > 1000 else 0.1,
        "is_new_customer": 0.3 if features["is_new_customer"] else 0.0,
    }
    return {
        "payload": {"feature_importances": features_importances},
        "summary": f"high amount ({features['amount']}) and new customer status increased fraud risk.",
    }


class FraudPredictionView(views.APIView):
    """
    POST /fraud-predict/

    Example integration of ml-audit in a DRF endpoint.
    """

    def post(self, request, *args, **kwargs):
        serializer = FraudRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        features = serializer.validated_data

        @audited_prediction(
            model_name="fraud_model",
            model_version="1.0.0",
            environment="prod",
            decision_field="is_fraud",
            confidence_field="fraud_probability",
            explanation_builder=build_fraud_explanation,
        )
        def predict_fraud(features, request):
            score = 0.1
            if features["amount"] > 1000:
                score += 0.4

            if features["is_new_customer"]:
                score += 0.2

            score = max(0.0, min(1.0, score))

            return {
                "fraud_probability": score,
                "is_fraud": score > 0.8,
            }

        result = predict_fraud(features, request)
        return result
