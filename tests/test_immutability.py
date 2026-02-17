from django.core.exceptions import ValidationError
from django.test import TestCase

from ml_audit.services import record_prediction_event


class ImmutabilityTest(TestCase):
    def test_prediction_event_is_immutable(self):
        event = record_prediction_event(
            model_name="test",
            model_version="1",
            features={"x": 1},
            output={"y": 2},
        )

        event.confidence = 0.9

        with self.assertRaises(ValidationError):
            event.save()

    def test_prediction_event_cannot_be_deleted(self):
        event = record_prediction_event(
            model_name="test",
            model_version="1",
            features={"x": 1},
            output={"y": 2},
        )

        with self.assertRaises(ValidationError):
            event.delete()
