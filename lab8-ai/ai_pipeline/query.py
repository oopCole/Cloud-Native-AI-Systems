"""RAG query: retrieve from Chroma, inject EVIDENCE block, call LLM via OpenAI-compatible client."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_DIR.parent
_VECTOR_DIR = _PACKAGE_DIR / "vector_store"
_PROMPTS_DIR = _PACKAGE_DIR / "prompts"
_COLLECTION_NAME = "documents"
_EVIDENCE_TOKEN = "<<<EVIDENCE>>>"

_RETRIEVAL_QUERY = {
    "summary": (
        "Business description operations segments products services revenue costs "
        "financial results MD&A management discussion analysis strategy outlook "
        "executive summary"
    ),
    "risks": (
        "risk factors uncertainties litigation regulatory compliance market competition "
        "operational financial liquidity forward-looking statements contingencies "
        "material risks"
    ),
}

_PROMPT_FILE = {
    "summary": "summary.md",
    "risks": "risks.md",
}


def load_prompt(name: str) -> str:
    """Load prompt text from ``ai_pipeline/prompts/{name}`` (e.g. ``summary.md``)."""
    path = _PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")


def _load_env() -> None:
    load_dotenv(_PROJECT_ROOT / ".env")


def _format_evidence_block(documents: list[str]) -> str:
    blocks: list[str] = []
    for i, doc in enumerate(documents, start=1):
        blocks.append(f"[Evidence chunk {i}]\n{doc}")
    return "\n\n".join(blocks)


def _inject_evidence(prompt_template: str, evidence_body: str) -> str:
    block = f"## EVIDENCE\n\n{evidence_body}"
    if _EVIDENCE_TOKEN in prompt_template:
        return prompt_template.replace(_EVIDENCE_TOKEN, block, 1)
    return f"{prompt_template.rstrip()}\n\n{block}\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="RAG query over ingested 10-K chunks.")
    parser.add_argument(
        "--task",
        required=True,
        choices=("summary", "risks"),
        help="summary: executive analytical summary; risks: material risk factors.",
    )
    args = parser.parse_args(argv)

    _load_env()
    provider = os.environ.get("EMBEDDING_PROVIDER", "sentence-transformers").strip().lower()
    if provider != "sentence-transformers":
        raise SystemExit(
            f"Unsupported EMBEDDING_PROVIDER={provider!r}; this lab uses sentence-transformers only."
        )
    try:
        top_k = int(os.environ["RAG_TOP_K"].strip())
    except (KeyError, ValueError) as exc:
        raise SystemExit("RAG_TOP_K must be set to an integer in .env") from exc
    embedding_model = os.environ.get("EMBEDDING_MODEL", "").strip()
    if not embedding_model:
        raise SystemExit("EMBEDDING_MODEL is missing in .env")

    api_key = (
        os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
    )
    base_url = (
        os.environ.get("OPENAI_BASE_URL", "").strip().rstrip("/")
        or os.environ.get("OPENROUTER_BASE_URL", "").strip().rstrip("/")
    )
    llm_model = os.environ.get("LLM_MODEL", "").strip() or os.environ.get(
        "OPENROUTER_MODEL", ""
    ).strip()

    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY or OPENROUTER_API_KEY in .env")
    if not base_url:
        raise SystemExit("Set OPENAI_BASE_URL or OPENROUTER_BASE_URL in .env")
    if not llm_model:
        raise SystemExit("Set LLM_MODEL (or OPENROUTER_MODEL) in .env")

    if not _VECTOR_DIR.is_dir():
        raise SystemExit(f"Vector store not found at {_VECTOR_DIR}. Run ingest first.")

    chroma = chromadb.PersistentClient(path=str(_VECTOR_DIR))
    try:
        collection = chroma.get_collection(_COLLECTION_NAME)
    except Exception as exc:
        raise SystemExit(f"Chroma collection '{_COLLECTION_NAME}' missing. Run ingest. ({exc})") from exc

    embedder = SentenceTransformer(embedding_model)
    query_text = _RETRIEVAL_QUERY[args.task]
    q_vec = embedder.encode([query_text], normalize_embeddings=True).tolist()[0]

    result = collection.query(
        query_embeddings=[q_vec],
        n_results=top_k,
        include=["documents"],
    )
    docs = result.get("documents") or []
    chunks = docs[0] if docs else []
    if not chunks:
        raise SystemExit("Retrieval returned no documents.")

    template = load_prompt(_PROMPT_FILE[args.task])
    evidence_body = _format_evidence_block(chunks)
    user_message = _inject_evidence(template, evidence_body)

    referer = os.environ.get("OPENROUTER_HTTP_REFERER", "https://localhost").strip()
    title = os.environ.get("OPENROUTER_APP_TITLE", "lab8-ai").strip()
    llm = OpenAI(
        base_url=base_url,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": referer,
            "X-Title": title,
            "X-OpenRouter-Title": title,
        },
    )
    max_out = os.environ.get("LLM_MAX_OUTPUT_TOKENS", "8192").strip()
    try:
        max_tokens = int(max_out)
    except ValueError:
        max_tokens = 8192

    completion = llm.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": user_message}],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    choice = completion.choices[0]
    content = choice.message.content
    if getattr(choice, "finish_reason", None) == "length":
        print(
            "Warning: response hit max length (LLM_MAX_OUTPUT_TOKENS); "
            "increase it in .env or shorten the prompt.",
            file=sys.stderr,
        )
    print(content if content else "")


if __name__ == "__main__":
    main()
