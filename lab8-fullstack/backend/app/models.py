from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IngestJsonBody(BaseModel):
    """Use when PDF is already on disk in the raw volume."""

    filename: str = Field(..., min_length=1, description="PDF filename under raw data directory")


class IngestResponse(BaseModel):
    source_pdf: str
    chunk_count: int
    embedding_model: str
    vector_dir: str


class EvidenceItem(BaseModel):
    chunk_id: str
    excerpt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyzeRequest(BaseModel):
    task: Literal["summary", "risks"]
    filing_id: str = Field(..., min_length=1, description="PDF filename, e.g. tesla_10K.pdf")


class AnalyzeResponse(BaseModel):
    task: str
    filing_id: str
    answer: str
    evidence: list[EvidenceItem]
    prompt_version: str
    model: str
