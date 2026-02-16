# ml-audit


<p align="left">
  <a href="https://github.com/sponsors/RJ-Gamer">
    <img src="https://img.shields.io/badge/Sponsor-GitHub-ff69b4?logo=github" alt="Sponsor on GitHub">
  </a>
</p>


[![PyPI version](https://img.shields.io/pypi/v/ml-audit.svg)](https://pypi.org/project/ml-audit/)
[![Python versions](https://img.shields.io/pypi/pyversions/ml-audit.svg)](https://pypi.org/project/ml-audit/)
[![Django versions](https://img.shields.io/badge/django-5.x-blue.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest%20%2B%20pytest--django-green.svg)](https://docs.pytest.org/)

Django-based toolkit for **auditing ML predictions** in production systems.

`ml-audit` helps you keep a **defensible, queryable trail** of every ML prediction your Django app makes:

- Who requested the prediction (user / service / tenant).
- Which model and version served it.
- What inputs (safely **redacted**) and outputs were used.
- What local explanation (e.g. SHAP/LIME) justifies the decision.

It is designed for **regulated and high-trust environments** (fintech, healthcare, B2B SaaS) where you must answer:

> “What did the model do here, why, and under which context?” months after deployment.

---

## Features

- 🧩 **Django-native reusable app**  
  Install into any Django project; no extra services or infra required.[web:114][web:117]

- 🧾 **Structured prediction events**  
  Stores model version, environment, redacted features, outputs, confidence, status, latency, and metadata.[web:293]

- 👤 **Requesting actor tracking**  
  Links each prediction to the user/service/API key and optional tenant, IP, and auth context.[web:235]

- 🔍 **Per-prediction explanations**  
  Attach SHAP/LIME/custom explanations (JSON payload + human-readable summary) to individual predictions.[web:15][web:225]

- 🛡️ **Redaction-first design**  
  Safe-by-default field-based redaction for feature payloads, configurable allowlist/denylist, sensible defaults for PII-like fields.[web:50][web:54][web:185][web:187]

- 📡 **Read-only REST API + admin**  
  DRF `ReadOnlyModelViewSet` endpoints and Django admin views for exploring predictions, models, and explanations.[web:203][web:207]

- 🧪 **Framework-agnostic explanations**  
  You bring SHAP/LIME/any XAI library; `ml-audit` gives you a consistent home for the explanation artifacts.[web:15][web:225][web:228]

---

## When should you use `ml-audit`?

Use `ml-audit` if:

- You serve ML models from **Django/DRF** and need **per-request traceability**, not just metrics.[web:114][web:199]
- You must answer user or regulator questions like  
  *“Why was this transaction flagged as fraud on this date?”*.[web:225]
- You want a **self-hosted, open-source** audit trail rather than pushing everything into a vendor’s black-box logs.[web:219][web:224]
- You care about **keeping PII out of generic logs**, but still need rich context for investigations.[web:50][web:54][web:185][web:187]

If you primarily need:

- Experiment tracking → MLflow, W&B, Neptune, etc.[web:217][web:219]  
- Model monitoring & drift → WhyLabs/whylogs, Seldon, Fiddler, etc.[web:223][web:227][web:229]  
- Fairness/offline analysis → Aequitas and similar toolkits.[web:221]  

You can still use `ml-audit` **alongside** those tools as your Django-side prediction audit log.

---

## Installation

Requirements:

- Python **3.11+**
- Django **5.x**
- PostgreSQL recommended for production (SQLite fine for dev/tests).

Install from PyPI:

```bash
pip install django-ml-audit
```

If DRF is optional:

```bash
pip install django-ml-audit[drf]
```

Add to INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "ml_audit",
]
```

Run migrations:

```bash
python manage.py migrate ml_audit
```

Mount the API (optional, read-only) in your project urls.py:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("api/ml-audit/", include("ml_audit.api.urls")),
]
```

---

## Quickstart: record and explain a prediction

1. Record a prediction in a Django view or service

```python
from ml_audit.services import ActorPayload, record_prediction_event

def predict_view(request):
    user = request.user if request.user.is_authenticated else None

    features = {
        "age": 42,
        "income": 100_000,
        "email": "user@example.com",  # will be redacted by default
    }

    # Call your model (example)
    score = 0.87
    output = {"score": score, "is_fraud": score > 0.8}

    actor = None
    if user:
        actor = ActorPayload(
            actor_type="user",
            actor_id=str(user.pk),
            tenant_id=getattr(user, "tenant_id", None),
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

    prediction = record_prediction_event(
        model_name="fraud_detector",
        model_version="1.0.0",
        features=features,
        output=output,
        decision_outcome="flagged" if output["is_fraud"] else "clean",
        confidence=score,
        actor=actor,
        environment="prod",
        trace_id=request.headers.get("X-Request-ID"),
        latency_ms=12.3,
    )

    # Use prediction.id (UUID) or prediction.prediction_id later to attach explanations
    ...
```

By default, fields like email, password, token, credit_card, etc. are masked before being stored.[web:50][web:54][web:185][web:187]

2. Attach an explanation (e.g. SHAP) later

```python
from ml_audit.services import attach_explanation

def compute_and_attach_explanation(prediction, shap_values):
    explanation_payload = {
        "feature_importances": shap_values,  # your structure
    }

    attach_explanation(
        prediction=prediction,           # instance, UUID pk, or prediction_id string
        method="shap",
        payload=explanation_payload,
        summary_text="High transaction amount and recent account age contributed most.",
    )
```

---

## Data model overview

Core entities:

- ModelVersion – logical model name + version + framework + optional build/commit/config snapshot.[web:293]
- RequestingActor – who/what requested the prediction (user/service/API key/tenant).[web:235]
- PredictionEvent – a prediction call: redacted features, outputs, confidence, status, latency, environment, actor, model, trace_id, prediction_id.[web:293]
- Explanation – one explanation attached to a prediction (method + payload + summary + status).[web:15][web:225]

Each `PredictionEvent`:

- Has a UUID primary key (id).
- Has a prediction_id string usable as a stable external identifier.
- Belongs to a ModelVersion.
- Optionally belongs to a RequestingActor.
- Has at most one Explanation in v1.

---

## Redaction configuration

By default, `ml-audit` applies conservative redaction to feature keys that look sensitive.

You can configure this in your Django settings:

```python
ML_AUDIT_REDACTION = {
    "ALLOWLIST": ["age", "income", "country"],   # stored as-is
    "DENYLIST": ["national_id", "raw_email"],    # always masked
    "MASK_VALUE": "[redacted]",                  # default: "****"
}
```

Behavior:

- Keys in `ALLOWLIST` → kept as-is.
- Keys in `DENYLIST` → replaced with MASK_VALUE.
- Keys matching built-in sensitive names (`password`, `token`, `email`, `phone`, `credit_card`, etc.) → masked unless explicitly allowlisted.[web:50][web:54][web:185][web:187]

⚠️ Redaction is applied only to the `features` field. 
`output`, `metadata`, and `auth_context` are stored as provided.
Ensure you handle sensitive data appropriately in those fields.

---

## API endpoints (read-only)

Once you include `ml_audit.api.urls`, you get (under your chosen prefix, e.g. /api/ml-audit/):

`GET /predictions/`
List prediction events with filters:

* `model_name`, `model_version`
* `actor_type`, `actor_id`, `tenant_id`
* `time_from`, `time_to` (ISO datetime)
* `decision_outcome`
* `environment`
* `has_explanation` (true/false)
* `status`
* `min_confidence`, `max_confidence`

Response body is a paginated list of predictions with nested model, actor, and explanation.

`GET /predictions/{uuid}/`
Retrieve a single prediction (by UUID pk) with nested model, actor, and explanation.

`GET /models/`
Browse known model versions.

All endpoints are read-only in v1.

---

## Sample DRF view (examples)
A complete DRF integration example is available in the repo under:

```text
examples/sample_drf_views.py
```
It shows how to:

* Validate request payload.
* Call a model.
* Build an `ActorPayload`.
* Call `record_prediction_event` and `attach_explanation`.
* Return a response including the prediction UUID.

---

## Testing
This repo uses pytest and pytest-django.[web:294]

From the project root:

```bash
python -m venv env
source env/bin/activate  # Windows: .\env\Scripts\activate
pip install pytest pytest-django
pytest
```

The provided pytest.ini is configured to:

- Use tests.settings as the Django settings module.
- Add the project root to PYTHONPATH.
- Use an in-memory SQLite database for tests.

---

## Versioning
`ml-audit` uses semantic versioning:

 - `0.y.z` – early development; APIs may change.
 - `1.y.z` – stable public API; breaking changes bump the major version.[web:301][web:304][web:307]

Version `0.1.0` is the first usable release; you can adopt it now, but expect possible breaking changes before `1.0.0`.

---

## Status
ml-audit is currently early-stage.
APIs and models may still evolve until v1.0. Feedback and contributions are welcome.

---

## Design guarantees (v0.1.x)

- Prediction events are append-only through the public API.
- `prediction_id` is stable and idempotent.
- Exactly one explanation per prediction (v1 constraint).
- No write REST endpoints (writes happen via Python API).
- Read API is paginated and read-only.

---

## License

This project is licensed under the MIT License – see LICENSE for details.[web:318][web:315]


