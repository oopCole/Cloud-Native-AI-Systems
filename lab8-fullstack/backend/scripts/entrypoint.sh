#!/bin/sh
set -e
cd /srv/backend
python - <<'PY'
import os, sys, time
import psycopg
url = os.environ.get("DATABASE_URL", "")
if not url:
    print("DATABASE_URL missing", file=sys.stderr)
    sys.exit(1)
for i in range(90):
    try:
        psycopg.connect(url, connect_timeout=3).close()
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("Postgres not reachable", file=sys.stderr)
sys.exit(1)
PY
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
