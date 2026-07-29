import pytest
from fastapi import status


def test_health_endpoint(test_client):
    r = test_client.get("/health")
    assert r.status_code == status.HTTP_200_OK
    assert r.json().get("status") == "ok"


@pytest.mark.skipif(True, reason="Requires full app endpoints")
def test_full_user_flow():
    # Placeholder for developer to wire real e2e tests
    assert True
