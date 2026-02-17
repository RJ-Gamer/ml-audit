# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.

---

## [0.1.0] - 2026-02-16

### Added
- Core models: ModelVersion, PredictionEvent, RequestingActor, Explanation
- Atomic and idempotent `record_prediction_event`
- Explanation attachment service
- Field-based redaction engine
- Read-only DRF API with filtering and pagination
- Django admin integration

### Changed
- Enforced external `prediction_id` semantics
- Improved DRF decorator to preserve original exceptions
- Made DRF an optional dependency

### Fixed
- Idempotency race condition on duplicate `prediction_id`
- Inconsistent redaction logic
- DRF integration identifier handling

---

## [0.2.0] - 2026-02-17

### Added
- Application-level immutability enforcement for `PredictionEvent`
- Admin hardening (no add/delete, read-only fields)

### Changed
- PredictionEvent now raises ValidationError on update or delete
- Strengthened append-only ledger semantics

---