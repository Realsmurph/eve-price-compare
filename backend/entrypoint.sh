#!/bin/sh
set -eu

python -m backend.migration_preflight
python -m alembic upgrade head
exec uvicorn backend.app:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"
