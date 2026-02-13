from rest_framework import serializers

from ml_audit.models import Explanation, ModelVersion, PredictionEvent, RequestingActor


class ModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelVersion
        fields = [
            "id",
            "model_name",
            "version",
            "framework",
            "build_id",
            "commit_hash",
            "config_snapshot",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RequestingActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestingActor
        fields = [
            "id",
            "actor_type",
            "actor_id",
            "tenant_id",
            "ip_address",
            "user_agent",
            "auth_context",
            "created_at",
        ]
        read_only_fields = fields


class explanationSerializer(serializers.ModelSerializer):
    prediction_id = serializers.UUIDField(source="prediction.id", read_only=True)

    class Meta:
        model = Explanation
        fields = [
            "id",
            "prediction_id",
            "method",
            "method_version",
            "payload",
            "summary_text",
            "status",
            "generated_at",
            "created_at",
        ]

        read_only_fields = fields


class PredictionEventSerializer(serializers.ModelSerializer):
    model = ModelVersionSerializer(read_only=True)
    actor = RequestingActorSerializer(read_only=True)
    explanation = explanationSerializer(read_only=True)

    class Meta:
        model = PredictionEvent
        fields = [
            "id",
            "prediction_id",
            "timestamp",
            "trace_id",
            "environment",
            "model",
            "actor",
            "features",
            "input_fingerprint",
            "output",
            "confidence",
            "decision_outcome",
            "status",
            "latency_ms",
            "metadata",
            "explanation",
        ]
        read_only_fields = fields
