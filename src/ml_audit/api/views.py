# src/ml_audit/api/views.py

from __future__ import annotations

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from ml_audit.api.serializers import ModelVersionSerializer, PredictionEventSerializer
from ml_audit.models import ModelVersion, PredictionEvent


class PredictionEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to prediction events.

    Supports filtering via query params:
    - model_name, model_version
    - actor_type, actor_id, tenant_id
    - time_from, time_to (ISO datetime)
    - decision_outcome
    - environment
    - has_explanation (true/false)
    - status
    - min_confidence, max_confidence
    """

    serializer_class = PredictionEventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = (
        PredictionEvent.objects.select_related("model", "actor")
        .prefetch_related("explanation")
        .order_by("-timestamp")
    )

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        model_name = params.get("model_name")
        if model_name:
            qs = qs.filter(model__model_name=model_name)

        model_version = params.get("model_version")
        if model_version:
            qs = qs.filter(model__version=model_version)

        actor_type = params.get("actor_type")
        if actor_type:
            qs = qs.filter(actor__actor_type=actor_type)

        actor_id = params.get("actor_id")
        if actor_id:
            qs = qs.filter(actor__actor_id=actor_id)

        tenant_id = params.get("tenant_id")
        if tenant_id:
            qs = qs.filter(actor__tenant_id=tenant_id)

        environment = params.get("environment")
        if environment:
            qs = qs.filter(environment=environment)

        decision_outcome = params.get("decision_outcome")
        if decision_outcome:
            qs = qs.filter(decision_outcome=decision_outcome)

        status_value = params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)

        has_explanation = params.get("has_explanation")
        if has_explanation is not None:
            val = has_explanation.lower()
            if val in {"true", "1", "yes"}:
                qs = qs.filter(explanation__isnull=False)
            elif val in {"false", "0", "no"}:
                qs = qs.filter(explanation__isnull=True)

        min_conf = params.get("min_confidence")
        if min_conf is not None:
            try:
                qs = qs.filter(confidence__gte=float(min_conf))
            except ValueError:
                pass

        max_conf = params.get("max_confidence")
        if max_conf is not None:
            try:
                qs = qs.filter(confidence__lte=float(max_conf))
            except ValueError:
                pass

        time_from = params.get("time_from")
        if time_from:
            try:
                dt_from = timezone.datetime.fromisoformat(time_from)
                if timezone.is_naive(dt_from):
                    dt_from = timezone.make_aware(dt_from, timezone.utc)
                qs = qs.filter(timestamp__gte=dt_from)
            except ValueError:
                pass

        time_to = params.get("time_to")
        if time_to:
            try:
                dt_to = timezone.datetime.fromisoformat(time_to)
                if timezone.is_naive(dt_to):
                    dt_to = timezone.make_aware(dt_to, timezone.utc)
                qs = qs.filter(timestamp__lte=dt_to)
            except ValueError:
                pass

        return qs


class ModelVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to model versions.
    """

    serializer_class = ModelVersionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = ModelVersion.objects.all().order_by("model_name", "version")
