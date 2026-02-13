from __future__ import annotations

import uuid
from typing import Any, Dict, Optional, Union

from django.utils import timezone

from ml_audit.models import Explanation, PredictionEvent, PredictionStatus

PredictionRef = Union[uuid.UUID, str, PredictionEvent]


def _resolve_prediction(ref: PredictionRef) -> PredictionEvent:
    if isinstance(ref, PredictionEvent):
        return ref

    if isinstance(ref, uuid.UUID):
        return PredictionEvent.objects.get(pk=ref)

    try:
        pk = uuid.UUID(ref)
    except (ValueError, TypeError):
        return PredictionEvent.objects.get(prediction_id=ref)

    return PredictionEvent.objects.get(pk=pk)


def attach_explanation(
    *,
    method: str,
    prediction: PredictionRef,
    payload: Dict[str, Any],
    summary_text: Optional[str] = None,
    status: PredictionStatus = PredictionStatus.SUCCESS,
    method_version: Optional[str] = None,
    generated_at=None,
) -> Explanation:
    prediction = _resolve_prediction(prediction)

    explanation, created = Explanation.objects.update_or_create(
        prediction=prediction,
        defaults={
            "method": method,
            "method_version": method_version or "",
            "payload": payload,
            "summary_text": summary_text or "",
            "status": status,
            "generated_at": generated_at or timezone.now(),
        },
    )
    return explanation
