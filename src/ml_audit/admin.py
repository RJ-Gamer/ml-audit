# src/ml_audit/admin.py

from __future__ import annotations

from django.contrib import admin

from ml_audit.models import Explanation, ModelVersion, PredictionEvent, RequestingActor


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "model_name",
        "version",
        "framework",
        "is_active",
        "created_at",
    )
    list_filter = (
        "framework",
        "is_active",
    )
    search_fields = (
        "id",
        "model_name",
        "version",
        "build_id",
        "commit_hash",
    )
    readonly_fields = ("id", "created_at")
    ordering = ("model_name", "version")


@admin.register(RequestingActor)
class RequestingActorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "actor_type",
        "actor_id",
        "tenant_id",
        "ip_address",
        "created_at",
    )
    list_filter = (
        "actor_type",
        "tenant_id",
    )
    search_fields = (
        "id",
        "actor_type",
        "actor_id",
        "tenant_id",
        "ip_address",
        "user_agent",
    )
    readonly_fields = ("id", "created_at")


@admin.register(PredictionEvent)
class PredictionEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "prediction_id",
        "timestamp",
        "model",
        "environment",
        "decision_outcome",
        "status",
        "confidence",
    )
    list_filter = (
        "environment",
        "status",
        "decision_outcome",
        "model__model_name",
        "model__version",
    )
    search_fields = (
        "id",
        "prediction_id",
        "trace_id",
        "model__model_name",
        "model__version",
        "actor__actor_id",
        "actor__tenant_id",
    )
    readonly_fields = (
        "id",
        "created_at",
        "timestamp",
    )
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)


@admin.register(Explanation)
class explanationnAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "prediction",
        "method",
        "status",
        "generated_at",
    )
    list_filter = (
        "method",
        "status",
    )
    search_fields = (
        "id",
        "prediction__id",
        "prediction__prediction_id",
        "method",
    )
    readonly_fields = (
        "id",
        "created_at",
        "generated_at",
    )
    ordering = ("-generated_at",)
