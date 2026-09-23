#!/bin/sh
# Azure App Service startup command: sh startup.sh
# Data (SQLite database, FS export cache) lives in /home, the only persistent directory.
set -e
cd "$(dirname "$0")"
if [ -f antenv/bin/activate ]; then . antenv/bin/activate; fi
DATA_DIR="${DATA_DIR:-/home/data}"
mkdir -p "$DATA_DIR"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$DATA_DIR/app.db}"
export FS_CACHE_DIR="${FS_CACHE_DIR:-$DATA_DIR/fs-exports}"
python -m alembic upgrade head
exec python -m uvicorn azure_app:app --host 0.0.0.0 --port "${PORT:-8000}" \
  --proxy-headers --forwarded-allow-ips="*"
