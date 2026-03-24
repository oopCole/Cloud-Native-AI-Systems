# Lab 8 full-stack (10-K RAG)

Integrates the standalone **`lab8-ai`** package (imported as `ai_pipeline`) with FastAPI, Postgres, Next.js, and Docker Compose.

## Layout

- `../lab8-ai/` — AI module only (no FastAPI code added there beyond `ai_pipeline/service.py`).
- `backend/` — FastAPI app, SQL schema, Dockerfile.
- `frontend/` — Next.js UI.
- `docker-compose.yml` — `db`, `backend`, `frontend` + volumes for Postgres, Chroma, and raw PDFs.

## Run with Docker

From this directory:

```bash
cp .env.example .env
# edit .env: set OPENROUTER_API_KEY and any model/RAG overrides

docker compose build
docker compose up
```

- API: `http://localhost:8000` (`GET /health`, `POST /api/filings/ingest`, `POST /api/filings/analyze`)
- UI: `http://localhost:3000` (the UI calls same-origin `/lab8-api/...`; Next.js proxies to the **`backend`** service on the Compose network.)
- Ingest: upload a PDF **or** JSON `{"filename":"existing.pdf"}` if the file is already in the `filings_raw` volume.
- Analyze: JSON `{"task":"summary"|"risks","filing_id":"your.pdf"}` — must match the PDF used at ingest.

Environment variables for RAG/LLM match **`lab8-ai`** (`RAG_TOP_K`, `CHUNK_*`, `EMBEDDING_*`, `LLM_MODEL`, OpenRouter keys, etc.).  
`LAB8_RAW_DIR` and `LAB8_VECTOR_DIR` are set in Compose for container paths.

## Local backend (optional)

```bash
cd ../lab8-ai && pip install -e .
cd ../lab8-fullstack/backend && pip install -e .
set DATABASE_URL=postgresql://...
set LAB8_RAW_DIR=...\lab8-ai\data\raw
set LAB8_VECTOR_DIR=...\lab8-ai\ai_pipeline\vector_store
uvicorn app.main:app --reload
```

Run from `backend/` so `app` resolves.
