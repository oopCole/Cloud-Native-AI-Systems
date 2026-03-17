from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row


def insert_summary(
    *,
    database_url: str,
    input_text: str,
    summary_text: str,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
) -> int:
    sql = """
    INSERT INTO summaries (
      input_text,
      summary_text,
      model,
      prompt_tokens,
      completion_tokens,
      total_tokens
    )
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
    """
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    input_text,
                    summary_text,
                    model,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("insert failed: no id returned")
            return int(row[0])


def fetch_recent_summaries(*, database_url: str, limit: int) -> list[dict[str, Any]]:
    sql = """
    SELECT
      id,
      input_text,
      summary_text,
      model,
      prompt_tokens,
      completion_tokens,
      total_tokens,
      created_at
    FROM summaries
    ORDER BY created_at DESC, id DESC
    LIMIT %s
    """
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            return list(cur.fetchall())

