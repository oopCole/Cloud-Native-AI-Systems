from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Load backend/.env when present.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH, override=False)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").strip()

# Lab-style LLM config compatibility:
# - prefer OPENAI_* when present (OpenRouter via OpenAI-compatible API)
# - fallback to OPENROUTER_* names used in prior labs
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "").strip()
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
).strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

AI_API_KEY = OPENAI_API_KEY or OPENROUTER_API_KEY
AI_BASE_URL = OPENAI_BASE_URL or OPENROUTER_BASE_URL
AI_MODEL = LLM_MODEL or OPENROUTER_MODEL or "mistralai/mistral-7b-instruct-v0.1"
