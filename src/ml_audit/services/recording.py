from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from ml_audit.conf import get_redaction_config
from ml_audit.models import (
    ModelVersion,
    PredictionEvent,
    PredictionStatus,
    RequestingActor,
)


@dataclass
class ActorPayload:
    """
    Simple typed wrapper for requesting actor data.
    """

    actor_type: str
    actor_id: str
    tenant_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    auth_token: Dict[str, Any] | None = None


def _get_or_create_model_version(
    *,
    model_name: str,
    model_version: str,
    framework: str | None = None,
    build_id: str | None = None,
    commit_hash: str | None = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
) -> ModelVersion:
    """Resolve or create a model version."""
    defaults: dict = {}
    if framework is not None:
        defaults["framework"] = framework
    if build_id is not None:
        defaults["build_id"] = build_id
    if commit_hash is not None:
        defaults["commit_hash"] = commit_hash
    if config_snapshot is not None:
        defaults["config_snapshot"] = config_snapshot

    obj, created = ModelVersion.objects.get_or_create(
        model_name=model_name,
        version=model_version,
        defaults=defaults,
    )

    return obj


def _get_or_create_actor(
    *, payload: Optional[ActorPayload]
) -> Optional[RequestingActor]:
    if payload is None:
        return None

    tenant_id = payload.tenant_id or ""

    obj, created = RequestingActor.objects.get_or_create(
        actor_type=payload.actor_type,
        actor_id=payload.actor_id,
        tenant_id=tenant_id,
        defaults={
            "ip_address": payload.ip_address,
            "user_agent": payload.user_agent or "",
            "auth_context": payload.auth_token,
        },
    )
    return obj


def _redact_features(features: Dict[str, Any]) -> Dict[str, Any]:
    config = get_redaction_config()
    redacted: Dict[str, Any] = {}

    for key, value in features.items():
        key_str = str(key)

        if config.is_sensitive(key_str):
            redacted[key_str] = config.mask_value
        else:
            redacted[key_str] = value

    return redacted


@transaction.atomic
def record_prediction_event(
    *,
    model_name: str,
    model_version: str,
    features: Dict[str, Any],
    output: Any,
    decision_outcome: str | None = None,
    actor: Optional[ActorPayload] = None,
    environment: str | None = None,
    trace_id: str | None = None,
    latency_ms: float | None = None,
    status: PredictionStatus = PredictionStatus.SUCCESS,
    confidence: float | None = None,
    metadata: Optional[Dict[str, Any]] = None,
    input_fingerprint: str | None = None,
    framework: str | None = None,
    build_id: str | None = None,
    commit_hash: str | None = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
    prediction_id: str | None = None,
    timestamp=None,
) -> PredictionEvent:
    """
    Record a prediction event in the audit log.
    """
    model_version_obj = _get_or_create_model_version(
        model_name=model_name,
        model_version=model_version,
        framework=framework,
        build_id=build_id,
        commit_hash=commit_hash,
        config_snapshot=config_snapshot,
    )

    requesting_actor = _get_or_create_actor(payload=actor)

    redacted_features = _redact_features(features)

    prediction_id = prediction_id or str(uuid.uuid4())

    prediction_event, created = PredictionEvent.objects.get_or_create(
        prediction_id=prediction_id,
        defaults={
            "model": model_version_obj,
            "actor": requesting_actor,
            "features": redacted_features,
            "output": output,
            "decision_outcome": decision_outcome or "",
            "environment": environment or "",
            "trace_id": trace_id or "",
            "latency_ms": latency_ms,
            "status": status,
            "confidence": confidence,
            "metadata": metadata or {},
            "input_fingerprint": input_fingerprint or "",
            "timestamp": timestamp or timezone.now(),
        },
    )

    return prediction_event
