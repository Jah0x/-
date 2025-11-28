import pytest
from app.core.config import get_settings
from app.services.outline_health_service import evaluate_status, OutlineHealthStatus


def test_evaluate_status_healthy():
    settings = get_settings()
    status = evaluate_status(100.0, None, settings)
    assert status == OutlineHealthStatus.healthy.value


def test_evaluate_status_degraded():
    settings = get_settings()
    status = evaluate_status(settings.outline_healthcheck_degraded_threshold_ms + 10, None, settings)
    assert status == OutlineHealthStatus.degraded.value


def test_evaluate_status_down_on_error():
    settings = get_settings()
    status = evaluate_status(None, "timeout", settings)
    assert status == OutlineHealthStatus.down.value
