from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Json


def insert_analysis_run(
    *,
    database_url: str,
    filing_identifier: str,
    task: str,
    prompt_version: str,
    retrieved_evidence: list[dict[str, Any]],
    output_text: str | None,
    error_message: str | None,
    llm_model: str | None,
    chunk_ids: list[str],
) -> int:
    sql = """
    INSERT INTO filing_analysis_runs (
      filing_identifier,
      task,
      prompt_version,
      retrieved_evidence,
      output_text,
      error_message,
      llm_model,
      chunk_ids
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    """
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    filing_identifier,
                    task,
                    prompt_version,
                    Json(retrieved_evidence),
                    output_text,
                    error_message,
                    llm_model,
                    chunk_ids,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("insert failed: no id returned")
            return int(row[0])
