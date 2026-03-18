import os
from pathlib import Path

from dotenv import load_dotenv

# load .env from lab4/ so it works when app is run from project root or lab4
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

def _clean_env(s: str) -> str:
    # remove BOM, CRLF, and take first line so .env quirks don't break the key
    if not s:
        return ""
    s = s.strip().split("\n")[0].split("\r")[0].strip()
    if s.startswith("\ufeff"):
        s = s[1:]
    return s


OPENROUTER_API_KEY = _clean_env(os.getenv("OPENROUTER_API_KEY", ""))
OPENROUTER_MODEL = _clean_env(os.getenv("OPENROUTER_MODEL", ""))
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
