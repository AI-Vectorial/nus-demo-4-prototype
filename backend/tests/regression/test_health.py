"""Regression suite -- OURS, and it must stay green.

This is what stops one table's merge from breaking the application for the other
four.  Tables add to tests/features/; nothing here is theirs to change.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_reports_ok():
    """The deployment-validation target Railway polls before routing traffic."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_healthz_reports_build_identity():
    """A failed rollout must be distinguishable from a stale one."""
    body = client.get("/healthz").json()
    assert "build" in body
    assert "environment" in body


def test_healthz_declares_dependencies_honestly():
    """Absent dependencies are reported, not omitted."""
    dependencies = client.get("/healthz").json()["dependencies"]
    assert {"database", "vector_store", "model"} <= set(dependencies)


def test_root_returns_service_identity():
    body = client.get("/").json()
    assert body["service"] == "m04-policy-assistant-api"
