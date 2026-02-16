from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from ml_audit.models import PredictionEvent


class DRFIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("testuser", "test@test.com", "pass")
        self.url = reverse("fraud-prediction")  # adjust to your URL name

    def test_audited_prediction(self):
        self.client.force_authenticate(user=self.user)
        
        data = {"amount": 1500, "is_new_customer": True, "email": "user@example.com"}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("prediction_id", response.data)
        
        prediction = PredictionEvent.objects.get(
            prediction_id=response.data["prediction_id"]
        )

        self.assertEqual(prediction.model.model_name, "fraud_model")
        self.assertEqual(prediction.status, "success")
        self.assertEqual(prediction.actor.actor_id, str(self.user.pk))
        self.assertEqual(prediction.status, "success")
        self.assertTrue(prediction.actor.actor_id == str(self.user.pk))
