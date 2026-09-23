"""Azure App Service entrypoint: API under /api and the built frontend on the same origin."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.main import app as api

# The deployment package places the Vite build (VITE_API_URL=/api) next to this file.
STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(static_dir: Path) -> FastAPI:
    site = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    site.mount("/api", api)
    if static_dir.is_dir():
        site.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
    return site


app = create_app(STATIC_DIR)
