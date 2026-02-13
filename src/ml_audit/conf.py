from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Set

from django.conf import settings


@dataclass(frozen=True)
class RedactionConfig:
    """
    Field-based redaction for structured feature dicts.

    - Fields in `allowlist` are stored as-is.
    - Fields in `denylist` are always masked.
    - Fields matching `default_sensitive_names` are masked unless explicitly allowed.
    """

    allowlist: Set[str] = field(default_factory=set)
    denylist: Set[str] = field(default_factory=set)
    mask_value: str = "*****"
    default_sensitive_names: Set[str] = field(
        default_factory=lambda: {
            "password",
            "passwd",
            "secret",
            "token",
            "access_token",
            "refresh_token",
            "ssn",
            "social_security_number",
            "credit_card",
            "card_number",
            "cvv",
            "email",
            "phone",
            "phone_number",
            "address",
        }
    )

    def is_sensitive(self, field_name: str) -> bool:
        if field_name in self.allowlist:
            return False
        if field_name in self.denylist:
            return True
        if any(sensitive in field_name for sensitive in self.default_sensitive_names):
            return True
        return False

    @classmethod
    def from_django_settings(cls) -> RedactionConfig:
        conf = getattr(settings, "ML_AUDIT_REDACTION", {})

        def _as_set(key: str) -> Set[str]:
            values: Iterable[str] = conf.get(key, [])
            return {str(v) for v in values}

        return cls(
            allowlist=_as_set("ALLOWLIST"),
            denylist=_as_set("DENYLIST"),
            mask_value=str(conf.get("MASK_VALUE", "*****")),
        )


def get_redaction_config() -> RedactionConfig:
    return RedactionConfig.from_django_settings()
