"""Importable RAG pipeline for backends: ingest and analyze without subprocess CLI."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from ai_pipeline.ingest import chunk_text, extract_pdf_text
from ai_pipeline.query import _format_evidence_block, _inject_evidence, load_prompt

_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_DIR.parent
_COLLECTION_NAME = "documents"

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

TaskName = Literal["summary", "risks"]


def _load_dotenv() -> None:
    """Load .env; if API keys are still empty, reload with override (Docker often sets OPENROUTER_API_KEY=)."""
    env_path = os.environ.get("LAB8_ENV_FILE", "").strip()
    file = Path(env_path) if env_path else _PROJECT_ROOT / ".env"
    load_dotenv(file, override=False)
    key = (
        os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
    )
    if not key and file.is_file():
        load_dotenv(file, override=True)


def raw_data_dir() -> Path:
    override = os.environ.get("LAB8_RAW_DIR", "").strip()
    return Path(override) if override else _PROJECT_ROOT / "data" / "raw"


def vector_store_dir() -> Path:
    override = os.environ.get("LAB8_VECTOR_DIR", "").strip()
    return Path(override) if override else _PACKAGE_DIR / "vector_store"


def prompts_dir() -> Path:
    return _PACKAGE_DIR / "prompts"


def compute_prompt_version() -> str:
    """Stable id from prompt file names + content hash."""
    h = hashlib.sha256()
    for name in ("summary.md", "risks.md"):
        p = prompts_dir() / name
        h.update(name.encode())
        h.update(p.read_bytes())
    return f"summary.md+risks.md:{h.hexdigest()[:16]}"


@dataclass
class EvidenceSnippet:
    chunk_id: str
    excerpt: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestResult:
    source_pdf: str
    chunk_count: int
    embedding_model: str
    vector_dir: str


@dataclass
class AnalyzeResult:
    task: TaskName
    filing_id: str
    answer: str
    evidence: list[EvidenceSnippet]
    prompt_version: str
    llm_model: str


class PipelineError(Exception):
    """User-facing pipeline failure."""


def _require_embedding_env() -> tuple[int, int, str]:
    provider = os.environ.get("EMBEDDING_PROVIDER", "sentence-transformers").strip().lower()
    if provider != "sentence-transformers":
        raise PipelineError(f"Unsupported EMBEDDING_PROVIDER={provider!r}")
    try:
        chunk_size = int(os.environ["CHUNK_SIZE"].strip())
        chunk_overlap = int(os.environ["CHUNK_OVERLAP"].strip())
    except (KeyError, ValueError) as exc:
        raise PipelineError("CHUNK_SIZE and CHUNK_OVERLAP must be integers in environment") from exc
    embedding_model = os.environ.get("EMBEDDING_MODEL", "").strip()
    if not embedding_model:
        raise PipelineError("EMBEDDING_MODEL is missing")
    return chunk_size, chunk_overlap, embedding_model


def _require_llm_env() -> tuple[str, str, str]:
    api_key = (
        os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
    )
    base_url = (
        os.environ.get("OPENAI_BASE_URL", "").strip().rstrip("/")
        or os.environ.get("OPENROUTER_BASE_URL", "").strip().rstrip("/")
    )
    llm_model = os.environ.get("LLM_MODEL", "").strip() or os.environ.get("OPENROUTER_MODEL", "").strip()
    if not api_key:
        raise PipelineError("Set OPENAI_API_KEY or OPENROUTER_API_KEY")
    if not base_url:
        raise PipelineError("Set OPENAI_BASE_URL or OPENROUTER_BASE_URL")
    if not llm_model:
        raise PipelineError("Set LLM_MODEL or OPENROUTER_MODEL")
    return api_key, base_url, llm_model


def run_ingest(*, filename: str | None = None) -> IngestResult:
    """
    Chunk + embed PDFs under LAB8_RAW_DIR (or package data/raw).
    If filename is set, ingest only that file; otherwise the first ``*.pdf`` lexicographically.
    """
    _load_dotenv()
    chunk_size, chunk_overlap, embedding_model = _require_embedding_env()
    raw_dir = raw_data_dir()
    vdir = vector_store_dir()

    if filename:
        pdf_path = raw_dir / filename
        if not pdf_path.is_file():
            raise PipelineError(f"PDF not found: {filename} under {raw_dir}")
    else:
        pdfs = sorted(raw_dir.glob("*.pdf"))
        if not pdfs:
            raise PipelineError(f"No PDF files in {raw_dir}")
        pdf_path = pdfs[0]

    text = extract_pdf_text(pdf_path)
    if not text.strip():
        raise PipelineError(f"No text extracted from {pdf_path.name}")

    parts = chunk_text(text, chunk_size, chunk_overlap)
    if not parts:
        raise PipelineError("No chunks produced")

    all_ids = [f"{pdf_path.stem}_{i}" for i in range(len(parts))]
    all_metadatas: list[dict] = [{"source": pdf_path.name, "chunk_index": i} for i in range(len(parts))]

    vdir.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(embedding_model)
    all_embeddings: list[list[float]] = []
    for i in range(0, len(parts), 64):
        batch = parts[i : i + 64]
        emb = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        all_embeddings.extend(emb.tolist())

    client = chromadb.PersistentClient(path=str(vdir))
    try:
        client.delete_collection(_COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=_COLLECTION_NAME,
        metadata={"embedding_model": embedding_model, "source_pdf": pdf_path.name},
    )
    for i in range(0, len(all_ids), 128):
        collection.add(
            ids=all_ids[i : i + 128],
            documents=parts[i : i + 128],
            embeddings=all_embeddings[i : i + 128],
            metadatas=all_metadatas[i : i + 128],
        )

    return IngestResult(
        source_pdf=pdf_path.name,
        chunk_count=len(parts),
        embedding_model=embedding_model,
        vector_dir=str(vdir.resolve()),
    )


def run_analyze(*, task: TaskName, filing_id: str, excerpt_max_chars: int = 500) -> AnalyzeResult:
    """
    Retrieve top-k for task, call LLM, return answer + evidence snippets.
    ``filing_id`` should match the stored PDF filename (metadata ``source``); if collection
    metadata does not match, analysis still runs on whatever is in the vector store.
    """
    _load_dotenv()
    provider = os.environ.get("EMBEDDING_PROVIDER", "sentence-transformers").strip().lower()
    if provider != "sentence-transformers":
        raise PipelineError(f"Unsupported EMBEDDING_PROVIDER={provider!r}")
    try:
        top_k = int(os.environ["RAG_TOP_K"].strip())
    except (KeyError, ValueError) as exc:
        raise PipelineError("RAG_TOP_K must be an integer") from exc
    embedding_model = os.environ.get("EMBEDDING_MODEL", "").strip()
    if not embedding_model:
        raise PipelineError("EMBEDDING_MODEL is missing")

    api_key, base_url, llm_model = _require_llm_env()
    vdir = vector_store_dir()
    if not vdir.is_dir():
        raise PipelineError(
            "Vector store missing. Run ingest first (POST /api/filings/ingest)."
        )

    chroma = chromadb.PersistentClient(path=str(vdir))
    try:
        collection = chroma.get_collection(_COLLECTION_NAME)
    except Exception as exc:
        raise PipelineError(
            "Chroma collection missing. Run ingest first (POST /api/filings/ingest)."
        ) from exc

    coll_meta = collection.metadata or {}
    stored_source = coll_meta.get("source_pdf")
    if stored_source and stored_source != filing_id:
        raise PipelineError(
            f"Vector store was built from {stored_source!r}, not {filing_id!r}. "
            "Run ingest again for this filing."
        )

    embedder = SentenceTransformer(embedding_model)
    q_vec = embedder.encode(
        [_RETRIEVAL_QUERY[task]], normalize_embeddings=True
    ).tolist()[0]

    result = collection.query(
        query_embeddings=[q_vec],
        n_results=top_k,
        include=["documents", "metadatas"],
    )
    ids_nested = result.get("ids") or []
    docs_nested = result.get("documents") or []
    meta_nested = result.get("metadatas") or []
    chunk_ids = ids_nested[0] if ids_nested else []
    docs = docs_nested[0] if docs_nested else []
    metas = meta_nested[0] if meta_nested else []
    if not docs:
        raise PipelineError("Retrieval returned no documents.")

    evidence: list[EvidenceSnippet] = []
    for i, doc in enumerate(docs):
        cid = chunk_ids[i] if i < len(chunk_ids) else str(i)
        meta = metas[i] if i < len(metas) else {}
        excerpt = (doc or "")[:excerpt_max_chars]
        if len(doc or "") > excerpt_max_chars:
            excerpt += "…"
        evidence.append(EvidenceSnippet(chunk_id=cid, excerpt=excerpt, metadata=dict(meta or {})))

    template = load_prompt(_PROMPT_FILE[task])
    evidence_body = _format_evidence_block(list(docs))
    user_message = _inject_evidence(template, evidence_body)

    max_out = os.environ.get("LLM_MAX_OUTPUT_TOKENS", "8192").strip()
    try:
        max_tokens = int(max_out)
    except ValueError:
        max_tokens = 8192

    referer = os.environ.get("OPENROUTER_HTTP_REFERER", "https://localhost").strip()
    title = os.environ.get("OPENROUTER_APP_TITLE", "lab8-fullstack").strip()
    llm = OpenAI(
        base_url=base_url,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": referer,
            "X-Title": title,
            "X-OpenRouter-Title": title,
        },
    )
    try:
        completion = llm.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.2,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        raise PipelineError(f"LLM request failed: {exc}") from exc

    content = completion.choices[0].message.content or ""

    return AnalyzeResult(
        task=task,
        filing_id=filing_id,
        answer=content.strip(),
        evidence=evidence,
        prompt_version=compute_prompt_version(),
        llm_model=llm_model,
    )


# re-export for type checkers
__all__ = [
    "AnalyzeResult",
    "EvidenceSnippet",
    "IngestResult",
    "PipelineError",
    "compute_prompt_version",
    "raw_data_dir",
    "run_analyze",
    "run_ingest",
    "vector_store_dir",
]
