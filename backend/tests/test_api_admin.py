from types import SimpleNamespace

import app.api.routes.admin as admin_routes


def _fake_settings(admin_token: str = "", football_data_api_key: str = "") -> SimpleNamespace:
    return SimpleNamespace(admin_token=admin_token, football_data_api_key=football_data_api_key)


def test_poll_live_returns_404_when_admin_token_not_configured(client, monkeypatch):
    monkeypatch.setattr(admin_routes, "get_settings", lambda: _fake_settings(admin_token=""))

    response = client.post("/api/v1/admin/poll-live")
    assert response.status_code == 404


def test_poll_live_returns_401_when_token_mismatched(client, monkeypatch):
    monkeypatch.setattr(admin_routes, "get_settings", lambda: _fake_settings(admin_token="secret"))

    response = client.post("/api/v1/admin/poll-live", headers={"X-Admin-Token": "wrong"})
    assert response.status_code == 401


def test_poll_live_calls_poller_and_returns_count_when_authorized(client, monkeypatch):
    monkeypatch.setattr(admin_routes, "get_settings", lambda: _fake_settings(admin_token="secret"))
    monkeypatch.setattr(admin_routes, "poll_live_matches", lambda db, client: ["fake-match"])

    response = client.post("/api/v1/admin/poll-live", headers={"X-Admin-Token": "secret"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "polled": 1}


def test_refresh_still_returns_401_when_token_mismatched(client, monkeypatch):
    # Regression guard: /admin/poll-live's guard was extracted from /admin/refresh's
    # inline check into _check_admin_token — this confirms /admin/refresh still works.
    monkeypatch.setattr(admin_routes, "get_settings", lambda: _fake_settings(admin_token="secret"))

    response = client.post("/api/v1/admin/refresh", headers={"X-Admin-Token": "wrong"})
    assert response.status_code == 401
