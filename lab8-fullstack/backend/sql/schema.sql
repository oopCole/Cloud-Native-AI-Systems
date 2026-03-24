CREATE TABLE IF NOT EXISTS filing_analysis_runs (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  filing_identifier TEXT NOT NULL,
  task TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  retrieved_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
  output_text TEXT,
  error_message TEXT,
  llm_model TEXT,
  chunk_ids TEXT[]
);

CREATE INDEX IF NOT EXISTS filing_analysis_runs_created_at_idx
  ON filing_analysis_runs (created_at DESC);
