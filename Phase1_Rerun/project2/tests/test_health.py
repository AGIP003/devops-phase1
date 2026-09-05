import pytest


@pytest.mark.no_database
@pytest.mark.critical
def test_health_uses_local_release_fallback(client, monkeypatch):
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["release"] == "local"
    assert "environment" in payload


@pytest.mark.no_database
@pytest.mark.critical
def test_health_reports_deployed_git_commit(client, monkeypatch):
    commit_sha = "2dae31f1234567890abcdef1234567890abcdef1"
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", commit_sha)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["release"] == commit_sha

