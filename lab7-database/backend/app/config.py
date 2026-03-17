import os
from pathlib import Path

from dotenv import load_dotenv

# load .env from lab4/ so it works when app is run from project root or lab4
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
