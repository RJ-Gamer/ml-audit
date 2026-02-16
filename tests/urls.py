from django.urls import path
from rest_framework.views import APIView

from ml_audit.integrations.drf import audited_prediction


class FraudPredictionView(APIView):

    @audited_prediction(
        model_name="fraud_model",
        model_version="1.0",
        decision_field="is_fraud",
    )
    def post(self, request):
        return {
            "is_fraud": True,
            "fraud_probability": 0.9,
        }


urlpatterns = [
    path("predict/", FraudPredictionView.as_view(), name="fraud-prediction"),
]

