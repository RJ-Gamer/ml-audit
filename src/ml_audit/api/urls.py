# src/ml_audit/api/urls.py

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ml_audit.api.views import ModelVersionViewSet, PredictionEventViewSet

router = DefaultRouter()
router.register(r"predictions", PredictionEventViewSet, basename="ml-audit-prediction")
router.register(r"models", ModelVersionViewSet, basename="ml-audit-model")

app_name = "ml_audit_api"

urlpatterns = [
    path("", include(router.urls)),
]
