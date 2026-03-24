#!/usr/bin/env python3
"""Wait for Postgres, then exec uvicorn (avoids CRLF issues with shell entrypoints on Windows)."""

from __future__ import annotations

import os
import sys
import time

import psycopg


def main() -> None:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL missing", file=sys.stderr)
        sys.exit(1)

    for _ in range(90):
        try:
            psycopg.connect(url, connect_timeout=3).close()
            break
        except Exception:
            time.sleep(1)
    else:
        print("Postgres not reachable", file=sys.stderr)
        sys.exit(1)

    os.chdir("/srv/backend")
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    main()
