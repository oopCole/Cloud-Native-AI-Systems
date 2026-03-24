# lab8-ai

AI techniques: prompt engineering, in-context learning, and RAG for 10-K analysis.

## Layout

- `ai_pipeline/` — ingestion, querying, and prompt templates
- `data/raw/` — place the 10-K PDF here
- `data/processed/` — optional scratch output from ingest
- `vector_store/` — populated when you run `ingest.py`

## Setup

Create a `.env` file in this directory (not committed) for API keys and paths as required by the lab.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```
