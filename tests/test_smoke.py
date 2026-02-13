# tests/test_smoke.py

import pytest


@pytest.mark.django_db
def test_import_and_migrate():
    import ml_audit  # noqa: F401
