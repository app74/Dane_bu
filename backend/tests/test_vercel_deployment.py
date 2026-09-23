"""Hosted (Vercel) behaviour: access control, /api mount, Postgres URL and FS lookup switch."""

import pytest
from fastapi.testclient import TestClient

from app import auth
from app.db import normalize_database_url
from app.main import RULES_PATH, app
from app.subject_lookup import fs_lookup_enabled
from vercel_app import app as vercel_app

PASSWORD = "spravne-heslo-123"
SECRET = "s" * 40


@pytest.fixture
def protected(monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", PASSWORD)
    monkeypatch.setenv("SESSION_SECRET", SECRET)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setattr(auth, "FAILED_LOGIN_DELAY", 0)


def test_local_api_stays_open_without_password(monkeypatch) -> None:
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    client = TestClient(app)
    assert client.get("/subjects").status_code == 200
    assert client.get("/auth/status").json() == {
        "enabled": False, "authenticated": True, "provider": None, "user": None,
    }


def test_protected_api_requires_login(protected) -> None:
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/subjects").status_code == 401
    assert client.get("/tax-rules").status_code == 401
    assert client.post("/subject-lookup", json={"identifier": "12345678"}).status_code == 401
    status = client.get("/auth/status").json()
    assert status["enabled"] is True and status["authenticated"] is False
    assert status["provider"] == "password"


def test_wrong_password_is_rejected(protected) -> None:
    client = TestClient(app)
    assert client.post("/auth/login", json={"password": "zle-heslo-12345"}).status_code == 401
    assert client.get("/subjects").status_code == 401


def test_login_sets_http_only_cookie_and_logout_clears_it(protected) -> None:
    client = TestClient(app)
    response = client.post("/auth/login", json={"password": PASSWORD})
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert client.get("/subjects").status_code == 200
    client.post("/auth/logout")
    assert client.get("/subjects").status_code == 401


def test_session_is_invalidated_by_password_change_and_expiry(protected, monkeypatch) -> None:
    token = auth.issue_token(now=1000)
    assert auth.valid_token(token, now=1001)
    assert not auth.valid_token(token, now=1000 + auth.SESSION_SECONDS + 1)
    assert not auth.valid_token("9999999999.podvrh")
    monkeypatch.setenv("APP_PASSWORD", "ine-spravne-heslo-456")
    assert not auth.valid_token(token, now=1001)


def test_vercel_without_configuration_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/subjects").status_code == 503
    assert client.post("/auth/login", json={"password": "x"}).status_code == 503


def test_short_password_is_refused(monkeypatch) -> None:
    monkeypatch.setenv("APP_PASSWORD", "kratke")
    monkeypatch.setenv("SESSION_SECRET", SECRET)
    assert TestClient(app).get("/subjects").status_code == 503


def test_vercel_mount_serves_api_under_prefix(protected) -> None:
    client = TestClient(vercel_app)
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/subjects").status_code == 401
    assert client.post("/api/auth/login", json={"password": PASSWORD}).status_code == 200
    assert client.get("/api/subjects").status_code == 200
    assert len(client.get("/api/tax-rules").json()) > 0
    assert client.get("/health").status_code == 404


def test_fs_lookup_is_off_on_vercel_by_default(monkeypatch) -> None:
    monkeypatch.delenv("FS_LOOKUP_ENABLED", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    assert fs_lookup_enabled()
    monkeypatch.setenv("VERCEL", "1")
    assert not fs_lookup_enabled()
    monkeypatch.setenv("FS_LOOKUP_ENABLED", "true")
    assert fs_lookup_enabled()


def test_disabled_fs_lookup_returns_manual_entry_hint(monkeypatch) -> None:
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("FS_LOOKUP_ENABLED", "0")
    response = TestClient(app).post("/subject-lookup", json={"identifier": "12345678"})
    assert response.status_code == 503
    assert "ručne" in response.json()["detail"]


@pytest.mark.parametrize(("url", "expected"), [
    ("postgres://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
    ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ("sqlite:///./app.db", "sqlite:///./app.db"),
])
def test_database_url_uses_psycopg_driver(url: str, expected: str) -> None:
    assert normalize_database_url(url) == expected


def test_rules_file_is_found() -> None:
    assert RULES_PATH.exists()


def test_cors_allows_configured_lan_origin(monkeypatch) -> None:
    from app.main import cors_origins

    monkeypatch.setenv("CORS_ORIGINS", "http://192.168.10.132:5173/, ,http://server:5173")
    assert cors_origins() == [
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://192.168.10.132:5173", "http://server:5173",
    ]
    monkeypatch.delenv("CORS_ORIGINS")
    assert cors_origins() == ["http://localhost:5173", "http://127.0.0.1:5173"]
