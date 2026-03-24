"""Ingest a single SEC 10-K PDF from data/raw into ChromaDB under ai_pipeline/vector_store."""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_DIR.parent
_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
_VECTOR_DIR = _PACKAGE_DIR / "vector_store"
_COLLECTION_NAME = "documents"


def _load_env() -> None:
    load_dotenv(_PROJECT_ROOT / ".env")


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into fixed-size windows with overlap (by character count)."""
    if chunk_size <= 0:
        raise ValueError("CHUNK_SIZE must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must satisfy 0 <= CHUNK_OVERLAP < CHUNK_SIZE")
    chunks: list[str] = []
    step = chunk_size - overlap
    n = len(text)
    start = 0
    while start < n:
        end = min(start + chunk_size, n)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start += step
    return chunks


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n\n".join(parts)


def main() -> None:
    _load_env()
    provider = os.environ.get("EMBEDDING_PROVIDER", "sentence-transformers").strip().lower()
    if provider != "sentence-transformers":
        raise SystemExit(
            f"Unsupported EMBEDDING_PROVIDER={provider!r}; this lab uses sentence-transformers only."
        )
    try:
        chunk_size = int(os.environ["CHUNK_SIZE"].strip())
        chunk_overlap = int(os.environ["CHUNK_OVERLAP"].strip())
    except (KeyError, ValueError) as exc:
        raise SystemExit("CHUNK_SIZE and CHUNK_OVERLAP must be set to integers in .env") from exc
    embedding_model = os.environ.get("EMBEDDING_MODEL", "").strip()
    if not embedding_model:
        raise SystemExit("EMBEDDING_MODEL is missing in .env")

    pdfs = sorted(_RAW_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDF files found in {_RAW_DIR}")

    pdf_path = pdfs[0]
    text = extract_pdf_text(pdf_path)
    if not text.strip():
        raise SystemExit(f"No text extracted from {pdf_path.name}")

    parts = chunk_text(text, chunk_size, chunk_overlap)
    if not parts:
        raise SystemExit("No text chunks produced from PDF")

    all_ids = [f"{pdf_path.stem}_{i}" for i in range(len(parts))]
    all_metadatas = [{"source": pdf_path.name, "chunk_index": i} for i in range(len(parts))]

    _VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(embedding_model)

    encode_batch = 64
    all_embeddings: list[list[float]] = []
    for i in range(0, len(parts), encode_batch):
        batch = parts[i : i + encode_batch]
        emb = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        all_embeddings.extend(emb.tolist())

    client = chromadb.PersistentClient(path=str(_VECTOR_DIR))
    try:
        client.delete_collection(_COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=_COLLECTION_NAME,
        metadata={"embedding_model": embedding_model, "source_pdf": pdf_path.name},
    )
    add_batch = 128
    for i in range(0, len(all_ids), add_batch):
        collection.add(
            ids=all_ids[i : i + add_batch],
            documents=parts[i : i + add_batch],
            embeddings=all_embeddings[i : i + add_batch],
            metadatas=all_metadatas[i : i + add_batch],
        )

    print(
        f"Ingested {len(parts)} chunks from {pdf_path.name} into {_VECTOR_DIR} "
        f"(embedding_model={embedding_model})"
    )


if __name__ == "__main__":
    main()
