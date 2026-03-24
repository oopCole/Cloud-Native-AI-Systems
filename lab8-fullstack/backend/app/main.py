from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import DATABASE_URL
from app.db import insert_analysis_run
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    EvidenceItem,
    IngestJsonBody,
    IngestResponse,
)

app = FastAPI(title="lab8-fullstack")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/filings/ingest", response_model=IngestResponse)
async def ingest_filing(request: Request) -> IngestResponse:
    """
    Multipart: form field ``file`` (PDF).  
    JSON: ``{ "filename": "name.pdf" }`` when the PDF already exists in the raw data directory.
    """
    from ai_pipeline.service import PipelineError, raw_data_dir, run_ingest

    raw_dir = raw_data_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)

    target_name: str | None = None
    ct = request.headers.get("content-type", "")

    if "multipart/form-data" in ct:
        form = await request.form()
        upload = form.get("file")
        if not isinstance(upload, UploadFile):
            raise HTTPException(
                status_code=400,
                detail="Missing form field 'file' (multipart PDF upload).",
            )
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Upload a .pdf file")
        target_name = Path(upload.filename).name
        dest = raw_dir / target_name
        try:
            contents = await upload.read()
            dest.write_bytes(contents)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc!s}") from exc
    else:
        try:
            data = await request.json()
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail='Send multipart form with field "file" or JSON body {"filename":"your.pdf"}',
            ) from exc
        try:
            body = IngestJsonBody.model_validate(data)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc!s}") from exc
        target_name = body.filename

    try:
        result = run_ingest(filename=target_name)
    except PipelineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc!s}") from exc

    return IngestResponse(
        source_pdf=result.source_pdf,
        chunk_count=result.chunk_count,
        embedding_model=result.embedding_model,
        vector_dir=result.vector_dir,
    )


@app.post("/api/filings/analyze", response_model=AnalyzeResponse)
def analyze_filing(body: AnalyzeRequest) -> AnalyzeResponse:
    from ai_pipeline.service import PipelineError, run_analyze

    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")

    evidence_payload: list[dict] = []
    chunk_ids: list[str] = []
    prompt_version = ""
    llm_model = ""

    try:
        result = run_analyze(task=body.task, filing_id=body.filing_id)
    except PipelineError as exc:
        msg = str(exc)
        try:
            insert_analysis_run(
                database_url=DATABASE_URL,
                filing_identifier=body.filing_id,
                task=body.task,
                prompt_version="(error before prompt version)",
                retrieved_evidence=[],
                output_text=None,
                error_message=msg,
                llm_model=None,
                chunk_ids=[],
            )
        except Exception:
            pass
        low = msg.lower()
        if "ingest first" in low or "vector store" in low or "collection missing" in low:
            raise HTTPException(
                status_code=409,
                detail=f"{msg} Use POST /api/filings/ingest first.",
            ) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        err = f"Analysis failed: {exc!s}"
        try:
            insert_analysis_run(
                database_url=DATABASE_URL,
                filing_identifier=body.filing_id,
                task=body.task,
                prompt_version="(error)",
                retrieved_evidence=[],
                output_text=None,
                error_message=err,
                llm_model=None,
                chunk_ids=[],
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=err) from exc

    prompt_version = result.prompt_version
    llm_model = result.llm_model
    for ev in result.evidence:
        evidence_payload.append(
            {
                "chunk_id": ev.chunk_id,
                "excerpt": ev.excerpt,
                "metadata": ev.metadata,
            }
        )
        chunk_ids.append(ev.chunk_id)

    try:
        insert_analysis_run(
            database_url=DATABASE_URL,
            filing_identifier=body.filing_id,
            task=body.task,
            prompt_version=prompt_version,
            retrieved_evidence=evidence_payload,
            output_text=result.answer,
            error_message=None,
            llm_model=llm_model,
            chunk_ids=chunk_ids,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis succeeded but database write failed: {exc!s}",
        ) from exc

    return AnalyzeResponse(
        task=result.task,
        filing_id=result.filing_id,
        answer=result.answer,
        evidence=[EvidenceItem(**x) for x in evidence_payload],
        prompt_version=prompt_version,
        model=llm_model,
    )
