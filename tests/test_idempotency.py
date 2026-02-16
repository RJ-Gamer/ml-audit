from django.test import TestCase

from ml_audit.services.recording import record_prediction_event


class IdempotencyTest(TestCase):
    def test_duplicate_prediction_id_returns_same_record(self):
        event1 = record_prediction_event(
            model_name="test",
            model_version="1",
            features={"x": 1},
            output={"y": 2},
            prediction_id="abc123",
        )
        

        event2 = record_prediction_event(
            model_name="test",
            model_version="1",
            features={"x": 1},
            output={"y": 2},
            prediction_id="abc123",
        )

        self.assertEqual(event1.id, event2.id)
