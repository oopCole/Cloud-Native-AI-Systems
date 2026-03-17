import httpx
from fastapi import Depends, FastAPI, HTTPException, Request

from app.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_URL,
)
from app.models import SummarizeRequest, SummarizeResponse

app = FastAPI(title="lab4")

DEV_TOKEN = "dev-token"


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

    return SummarizeResponse(
        summary=summary,
        model=OPENROUTER_MODEL or "mistralai/mistral-7b-instruct:free",
        truncated=truncated,
    )
