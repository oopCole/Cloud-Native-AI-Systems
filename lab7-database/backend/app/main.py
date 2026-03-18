import httpx
from fastapi import Depends, FastAPI, HTTPException, Request

from app.config import (
    DATABASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_URL,
)
from app.db import fetch_recent_summaries, insert_summary
from app.models import SummarizeRequest, SummarizeResponse, SummaryRow

app = FastAPI(title="lab4")

DEV_TOKEN = "dev-token"


@app.on_event("startup")
def _log_openrouter_status() -> None:
    import logging
    if OPENROUTER_API_KEY:
        ok = "sk-or-" in OPENROUTER_API_KEY[:10]
        logging.getLogger("uvicorn.access").info(
            f"OPENROUTER_API_KEY: set, length={len(OPENROUTER_API_KEY)}, looks_valid={ok}"
        )
    else:
        logging.getLogger("uvicorn.access").warning("OPENROUTER_API_KEY: not set")


def require_auth(request: Request) -> None:
    """raise 401 if Authorization: Bearer <token> is missing or token is not dev-token."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header; use Bearer <token>",
        )
    token = auth[7:].strip()
    if token != DEV_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(
    body: SummarizeRequest,
    _: None = Depends(require_auth),
) -> SummarizeResponse:
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is not set; check .env",
        )

    prompt = (
        f"Summarize the following text in at most {body.max_length} words. "
        f"Output only the summary, no preamble.\n\n{body.text}"
    )

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL or "mistralai/mistral-7b-instruct:free",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        raise HTTPException(
            status_code=503,
            detail=f"Upstream summarization failed: {e!s}",
        ) from e

    if "error" in data:
        raise HTTPException(
            status_code=503,
            detail=data["error"].get("message", str(data["error"])),
        )

    if "choices" not in data or not data["choices"]:
        raise HTTPException(
            status_code=503,
            detail="Upstream returned no choices",
        )

    raw = (data["choices"][0].get("message") or {}).get("content") or ""
    raw = raw.strip()
    words = raw.split()
    if len(words) > body.max_length:
        summary = " ".join(words[: body.max_length])
        truncated = True
    else:
        summary = raw
        truncated = False

    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL is not set",
        )

    usage = data.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")
    try:
        insert_summary(
            database_url=DATABASE_URL,
            input_text=body.text,
            summary_text=summary,
            model=OPENROUTER_MODEL or "mistralai/mistral-7b-instruct:free",
            prompt_tokens=int(prompt_tokens) if prompt_tokens is not None else None,
            completion_tokens=int(completion_tokens) if completion_tokens is not None else None,
            total_tokens=int(total_tokens) if total_tokens is not None else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"database insert failed: {e!s}",
        ) from e

    return SummarizeResponse(
        summary=summary,
        model=OPENROUTER_MODEL or "mistralai/mistral-7b-instruct:free",
        truncated=truncated,
    )


@app.get("/summaries", response_model=list[SummaryRow])
def summaries(
    limit: int = 20,
    _: None = Depends(require_auth),
) -> list[SummaryRow]:
    if limit <= 0 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")

    try:
        rows = fetch_recent_summaries(database_url=DATABASE_URL, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"database query failed: {e!s}") from e

    # pydantic will coerce created_at to string via json serialization
    return [SummaryRow(**row) for row in rows]
