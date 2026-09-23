"""Access control for hosted deployments.

- Locally (no APP_PASSWORD, not on a hosting platform) the API stays open as before.
- Shared password (APP_PASSWORD + SESSION_SECRET): required on Vercel, optional elsewhere.
- Azure App Service without APP_PASSWORD: Microsoft Entra ID via App Service
  authentication (Easy Auth). The platform injects X-MS-CLIENT-PRINCIPAL-* headers,
  which external requests cannot set; without them the API refuses to serve data.
Every hosted mode fails closed when it is not configured.
"""

import hashlib
import hmac
import os
import time

from fastapi import APIRouter, Body, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

COOKIE_NAME = "dane_session"
SESSION_SECONDS = 8 * 3600
MIN_PASSWORD_LENGTH = 12
MIN_SECRET_LENGTH = 32
FAILED_LOGIN_DELAY = 1.0
PUBLIC_PATHS = {"/health", "/auth/status", "/auth/login", "/auth/logout"}
PRINCIPAL_ID_HEADER = "x-ms-client-principal-id"
PRINCIPAL_NAME_HEADER = "x-ms-client-principal-name"

router = APIRouter(prefix="/auth")


def on_vercel() -> bool:
    return os.getenv("VERCEL") == "1"


def on_azure() -> bool:
    # App Service always defines WEBSITE_SITE_NAME for the running app.
    return bool(os.getenv("WEBSITE_SITE_NAME"))


def password() -> str:
    return os.getenv("APP_PASSWORD", "")


def secret() -> str:
    return os.getenv("SESSION_SECRET", "")


def provider() -> str | None:
    if password() or on_vercel():
        return "password"
    if on_azure():
        return "entra"
    return None


def auth_enabled() -> bool:
    return provider() is not None


def configuration_error() -> str | None:
    if provider() != "password":
        return None
    if len(password()) < MIN_PASSWORD_LENGTH:
        return f"Nastavte APP_PASSWORD s dĺžkou aspoň {MIN_PASSWORD_LENGTH} znakov."
    if len(secret()) < MIN_SECRET_LENGTH:
        return f"Nastavte SESSION_SECRET s dĺžkou aspoň {MIN_SECRET_LENGTH} znakov."
    return None


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode()).digest()


def _signature(expires: int) -> str:
    # Binding the password hash invalidates all sessions when the password changes.
    message = f"{expires}:{_digest(password()).hex()}".encode()
    return hmac.new(secret().encode(), message, hashlib.sha256).hexdigest()


def issue_token(now: float | None = None) -> str:
    expires = int((now if now is not None else time.time()) + SESSION_SECONDS)
    return f"{expires}.{_signature(expires)}"


def valid_token(token: str | None, now: float | None = None) -> bool:
    if not token or "." not in token:
        return False
    expires_text, signature = token.split(".", 1)
    if not expires_text.isdigit():
        return False
    expires = int(expires_text)
    if expires < (now if now is not None else time.time()):
        return False
    return hmac.compare_digest(signature, _signature(expires))


def authenticated(request: Request) -> bool:
    mode = provider()
    if mode == "password":
        return valid_token(request.cookies.get(COOKIE_NAME))
    if mode == "entra":
        return bool(request.headers.get(PRINCIPAL_ID_HEADER))
    return True


def route_path(request: Request) -> str:
    """Path inside this app, also when it is mounted under /api on Vercel or Azure."""
    path = request.scope["path"]
    root = request.scope.get("root_path", "")
    if root and path.startswith(root):
        path = path[len(root):] or "/"
    return path


def secure_cookie(request: Request) -> bool:
    forwarded = request.headers.get("x-forwarded-proto", "")
    return on_vercel() or request.url.scheme == "https" or forwarded == "https"


@router.get("/status")
def status(request: Request) -> dict[str, bool | str | None]:
    signed_in = authenticated(request)
    user = request.headers.get(PRINCIPAL_NAME_HEADER) if provider() == "entra" else None
    return {
        "enabled": auth_enabled(),
        "authenticated": signed_in,
        "provider": provider(),
        "user": user if signed_in else None,
    }


@router.post("/login")
def login(
    request: Request, response: Response, password_input: str = Body(
        embed=True, alias="password", max_length=200)
) -> dict[str, bool]:
    mode = provider()
    if mode is None:
        return {"authenticated": True}
    if mode == "entra":
        raise HTTPException(400, "Prihlásenie prebieha cez účet Microsoft.")
    if not hmac.compare_digest(_digest(password_input), _digest(password())):
        time.sleep(FAILED_LOGIN_DELAY)
        raise HTTPException(401, "Nesprávne heslo.")
    response.set_cookie(
        COOKIE_NAME, issue_token(), max_age=SESSION_SECONDS, httponly=True,
        secure=secure_cookie(request), samesite="strict", path="/",
    )
    return {"authenticated": True}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    response.delete_cookie(
        COOKIE_NAME, path="/", httponly=True, secure=secure_cookie(request), samesite="strict"
    )
    return {"authenticated": False}


def install(app: FastAPI) -> None:
    app.include_router(router)

    @app.middleware("http")
    async def require_session(request: Request, call_next):
        path = route_path(request)
        if path == "/health" or request.method == "OPTIONS":
            return await call_next(request)
        error = configuration_error()
        if error:
            return JSONResponse({"detail": f"Aplikácia nie je nakonfigurovaná. {error}"}, 503)
        if path not in PUBLIC_PATHS and not authenticated(request):
            return JSONResponse({"detail": "Prihláste sa."}, 401)
        return await call_next(request)
