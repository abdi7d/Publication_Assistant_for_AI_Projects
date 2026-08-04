from fastapi.testclient import TestClient

from app import app
from security.configs.config_loader import settings


client = TestClient(app)


def test_health_endpoints_are_available():
    health = client.get("/health")
    assert health.status_code == 200
    payload = health.json()
    assert payload["status"] == "ok"
    assert payload["service"]

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    live = client.get("/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"


def test_core_runtime_settings_are_initialized():
    assert settings.APP_NAME
    assert settings.APP_ENV in {"development", "production", "staging"}
    assert settings.RATE_LIMIT_PER_MINUTE > 0
    assert settings.MAX_UPLOAD_BYTES > 0
