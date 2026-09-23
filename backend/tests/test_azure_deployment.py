"""Azure App Service: Microsoft Entra ID (Easy Auth) headers, static frontend, /home paths."""

import pytest
from fastapi.testclient import TestClient

from app import subject_lookup
from app.main import app
from app.subject_lookup import fs_lookup_enabled
from azure_app import create_app

ENTRA_USER = {
    "X-MS-CLIENT-PRINCIPAL-ID": "00000000-0000-0000-0000-000000000001",
    "X-MS-CLIENT-PRINCIPAL-NAME": "tester@example.com",
}


@pytest.fixture
def azure(monkeypatch):
    monkeypatch.setenv("WEBSITE_SITE_NAME", "dane-bu-test")
    for name in ("APP_PASSWORD", "SESSION_SECRET", "VERCEL", "FS_LOOKUP_ENABLED"):
        monkeypatch.delenv(name, raising=False)


def test_azure_without_entra_headers_refuses_data(azure) -> None:
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/subjects").status_code == 401
    assert client.get("/tax-rules").status_code == 401
    status = client.get("/auth/status").json()
    assert status == {"enabled": True, "authenticated": False, "provider": "entra", "user": None}


def test_azure_accepts_requests_authenticated_by_easy_auth(azure) -> None:
    client = TestClient(app, headers=ENTRA_USER)
    assert client.get("/subjects").status_code == 200
    status = client.get("/auth/status").json()
    assert status["authenticated"] is True and status["user"] == "tester@example.com"


def test_azure_ignores_empty_principal_header(azure) -> None:
    client = TestClient(app, headers={"X-MS-CLIENT-PRINCIPAL-ID": ""})
    assert client.get("/subjects").status_code == 401


def test_password_login_is_disabled_with_entra(azure) -> None:
    response = TestClient(app).post("/auth/login", json={"password": "cokolvek-dlhe-heslo"})
    assert response.status_code == 400


def test_app_password_takes_precedence_on_azure(azure, monkeypatch) -> None:
    monkeypatch.setenv("APP_PASSWORD", "spravne-heslo-123")
    monkeypatch.setenv("SESSION_SECRET", "s" * 40)
    client = TestClient(app, headers=ENTRA_USER)
    assert client.get("/auth/status").json()["provider"] == "password"
    assert client.get("/subjects").status_code == 401


def test_fs_lookup_stays_enabled_on_azure(azure) -> None:
    assert fs_lookup_enabled()


def test_fs_cache_dir_is_configurable(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FS_CACHE_DIR", str(tmp_path / "fs"))
    assert subject_lookup.cache_dir() == tmp_path / "fs"
    monkeypatch.delenv("FS_CACHE_DIR")
    assert subject_lookup.cache_dir().name == "dane-bu-fs-exports"


def test_site_serves_frontend_and_api_on_one_origin(azure, tmp_path) -> None:
    (tmp_path / "index.html").write_text("<h1>Platobné údaje</h1>", encoding="utf-8")
    client = TestClient(create_app(tmp_path), headers=ENTRA_USER)
    assert "Platobné údaje" in client.get("/").text
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/subjects").status_code == 200
    assert client.get("/api/auth/status").json()["provider"] == "entra"


def test_site_without_build_serves_only_api(azure, tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "missing"))
    assert client.get("/api/health").status_code == 200
    assert client.get("/").status_code == 404
