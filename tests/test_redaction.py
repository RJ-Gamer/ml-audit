from django.test import TestCase

from ml_audit.services.recording import record_prediction_event


class RedactionTest(TestCase):
    def test_email_is_masked(self):
        event = record_prediction_event(
            model_name="test",
            model_version="1",
            features={"email": "user@example.com"},
            output={"result": 1},
        )

        self.assertEqual(event.features["email"], "*****")
