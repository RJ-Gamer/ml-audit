import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class FrameworkChoice(models.TextChoices):
    SKLEARN = "sklearn"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    OTHER = "other"


class ActorTypeChoice(models.TextChoices):
    USER = "user"
    SERVICE = "service"
    API_KEY = "api_key"
    JOB = "job"
    OTHER = "other"


class PredictionStatus(models.TextChoices):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ModelVersion(models.Model):
    """
    Logical Model + Specific version used for prediction.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=64, db_index=True)
    framework = models.CharField(
        max_length=32, choices=FrameworkChoice.choices, default=FrameworkChoice.SKLEARN
    )
    build_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Identifier for build / training run / registry entry.",
    )
    commit_hash = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Source control commit hash associated with this model version.",
    )
    config_snapshot = models.JSONField(
        blank=True,
        null=True,
        help_text="Optional JSON snapshot of key model configuration.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("model_name", "version")
        indexes = [
            models.Index(fields=["model_name", "version"]),
        ]

    def __str__(self):
        return f"{self.model_name}: v{self.version}"


class RequestingActor(models.Model):
    """
    Who/what requested a prediction (user, service, API client, etc.).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_type = models.CharField(
        max_length=32,
        choices=ActorTypeChoice.choices,
        db_index=True,
    )
    actor_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Identifier of the actor in the host system (e.g. user ID, client ID).",
    )
    tenant_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Identifier of the tenant (e.g. customer, organization) in the host system.",
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, default="")
    auth_context = models.JSONField(
        blank=True,
        null=True,
        help_text="Optional JSON containing authentication/authorization context.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["actor_type", "actor_id"]),
            models.Index(fields=["tenant_id"]),
        ]

    def __str__(self) -> str:
        if self.tenant_id:
            return f"{self.actor_type}:{self.actor_id}@({self.tenant_id})"
        return f"{self.actor_type}:{self.actor_id}"


class PredictionEvent(models.Model):
    """
    One prediction call to a model: inputs (redacted), outputs, metadata.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prediction_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Stable external identifier for this prediction event.",
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the prediction was made (UTC).",
    )
    trace_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Optional correlation ID for tracing across services.",
    )
    environment = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="Environment where the prediction was made (e.g. 'production', 'staging').",
    )
    model = models.ForeignKey(
        ModelVersion,
        on_delete=models.PROTECT,
        related_name="prediction_events",
    )
    actor = models.ForeignKey(
        RequestingActor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="prediction_events",
    )
    features = models.JSONField(
        help_text="Redacted snapshot of model-ready features used for this prediction."
    )
    input_fingerprint = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Fingerprint of the input features (e.g. hash) for detecting data drift.",
    )
    output = models.JSONField(
        blank=True,
        null=True,
        db_index=True,
        help_text="Model output (e.g. prediction, score, probabilities).",
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional canonical confidence / probability score for the main outcome.",
    )
    decision_outcome = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Business-level outcome, e.g. 'approved', 'denied', 'fraud', etc.",
    )
    status = models.CharField(
        max_length=32,
        choices=PredictionStatus.choices,
        default=PredictionStatus.SUCCESS,
        db_index=True,
        help_text="Overall status of the prediction attempt.",
    )
    latency_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="Time taken for the prediction in milliseconds.",
    )
    metadata = models.JSONField(
        blank=True, null=True, help_text="Additional metadata about the prediction."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["confidence"]),
            models.Index(fields=["decision_outcome"]),
            models.Index(fields=["status"]),
            models.Index(fields=["environment"]),
        ]

    def __str__(self):
        return f"{self.model} - {self.prediction_id}"

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get('force_insert', False):
            raise ValidationError("PredictionEvent updates are not allowed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("PredictionEvent deletion is not allowed.")

class Explanation(models.Model):
    """
    Explanation attached to a specific prediction event.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prediction = models.OneToOneField(
        PredictionEvent,
        on_delete=models.CASCADE,
        related_name="explanation",
    )
    method = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Explanation method, e.g. 'shap', 'lime', 'custom_reason_codes'.",
    )
    method_version = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Version of the explanation method.",
    )
    payload = models.JSONField(
        help_text="Structured explanation payload (feature attributions etc.)."
    )
    summary_text = models.TextField(
        blank=True,
        default="",
        help_text="Human-readable summary of the explanation.",
    )
    status = models.CharField(
        max_length=32,
        choices=PredictionStatus.choices,
        default=PredictionStatus.SUCCESS,
        help_text="Status of the explanation generation.",
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["method"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Explanation for {self.prediction} via {self.method}"

    @property
    def prediction_id(self) -> str:
        return self.prediction.prediction_id
