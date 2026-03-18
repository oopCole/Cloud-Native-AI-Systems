#!/usr/bin/env python3
"""
sanity check: call OpenRouter with the given key and report success or error.
usage:
  python check_openrouter_key.py
  python check_openrouter_key.py <OPENROUTER_API_KEY>
  OPENROUTER_API_KEY=sk-or-... python check_openrouter_key.py
reads .env in this directory if no key is provided.
"""
import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("install httpx: pip install httpx", file=sys.stderr)
    sys.exit(1)

# load .env from script directory if present
_env = Path(__file__).resolve().parent / ".env"
if _env.exists():
    for line in _env.read_text().strip().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

KEY = os.environ.get("OPENROUTER_API_KEY", "").strip() or (
    sys.argv[1].strip() if len(sys.argv) > 1 else ""
)
URL = "https://openrouter.ai/api/v1/chat/completions"

if not KEY:
    print("error: no OPENROUTER_API_KEY (set env, pass as arg, or put in .env)", file=sys.stderr)
    sys.exit(1)

# mask key in output
mask = KEY[:12] + "..." + KEY[-4:] if len(KEY) > 20 else "***"

print(f"using key: {mask}")
print(f"POST {URL} ...")

try:
    r = httpx.post(
        URL,
        headers={
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
            "max_tokens": 10,
        },
        timeout=30.0,
    )
except Exception as e:
    print(f"request failed: {e}")
    sys.exit(1)

print(f"status: {r.status_code} {r.reason_phrase}")
if r.status_code == 200:
    data = r.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
    if isinstance(content, str):
        cleaned = content.strip()
    else:
        cleaned = ""
    print(f"response: {cleaned or data}")
    print("key is valid.")
else:
    print(f"body: {r.text[:500]}")
    print("key is invalid or request was rejected.")
    sys.exit(1)
