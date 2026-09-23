from conftest import client


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database_backend"] == "sqlite"
    assert body["durable_persistence"] is False


def test_readiness_reports_real_blockers():
    response = client.get("/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"]["ok"] is True
    assert body["database"]["backend"] == "sqlite"
    assert body["database"]["durable"] is False
    assert "durable_persistence_not_enabled" in body["blockers"]
    assert "validated_cv_artifacts_not_configured" in body["blockers"]
