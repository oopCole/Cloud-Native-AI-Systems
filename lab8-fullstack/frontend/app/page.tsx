"use client";

import { useState } from "react";

/** Same-origin proxy (/lab8-api → backend) avoids browser → localhost:8000 issues in Docker. */
const apiBase =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "/lab8-api";

type EvidenceItem = {
  chunk_id: string;
  excerpt: string;
  metadata: Record<string, unknown>;
};

async function errorMessageFromResponse(res: Response): Promise<string> {
  const text = await res.text();
  if (!text.trim()) {
    return `${res.status} ${res.statusText || "Error"} (empty body — is the API up?)`;
  }
  try {
    const data = JSON.parse(text) as { detail?: unknown };
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      return JSON.stringify(data.detail);
    }
  } catch {
    /* not JSON */
  }
  return `${res.status}: ${text.slice(0, 800)}`;
}

export default function Home() {
  const [task, setTask] = useState<"summary" | "risks">("summary");
  const [filingId, setFilingId] = useState("tesla_10K.pdf");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [answer, setAnswer] = useState("");
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [ingestMsg, setIngestMsg] = useState("");

  async function runIngest() {
    setError("");
    setIngestMsg("");
    setBusy(true);
    try {
      if (file) {
        const fd = new FormData();
        fd.append("file", file);
        const res = await fetch(`${apiBase}/api/filings/ingest`, {
          method: "POST",
          body: fd,
        });
        if (!res.ok) {
          setError(await errorMessageFromResponse(res));
          return;
        }
        const data = await res.json();
        setIngestMsg(
          `Ingested ${data.chunk_count} chunks from ${data.source_pdf} (${data.embedding_model}).`,
        );
        setFilingId(data.source_pdf);
      } else {
        const res = await fetch(`${apiBase}/api/filings/ingest`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename: filingId }),
        });
        if (!res.ok) {
          setError(await errorMessageFromResponse(res));
          return;
        }
        const data = await res.json();
        setIngestMsg(
          `Ingested ${data.chunk_count} chunks from ${data.source_pdf} (${data.embedding_model}).`,
        );
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runAnalyze() {
    setError("");
    setAnswer("");
    setEvidence([]);
    setBusy(true);
    try {
      const res = await fetch(`${apiBase}/api/filings/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, filing_id: filingId }),
      });
      if (!res.ok) {
        setError(await errorMessageFromResponse(res));
        return;
      }
      const data = await res.json();
      setAnswer(data.answer ?? "");
      setEvidence(Array.isArray(data.evidence) ? data.evidence : []);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ padding: "2rem", maxWidth: "960px", margin: "0 auto" }}>
      <h1>10-K analysis</h1>
      <p style={{ color: "#444" }}>
        API: <code>{apiBase}</code> — ingest builds the vector index; analyze runs RAG + LLM.
      </p>

      <section style={{ marginBottom: "2rem" }}>
        <h2>1. Ingest</h2>
        <p>
          Upload a PDF <strong>or</strong> enter a filename that already exists in the backend{" "}
          <code>/data/raw</code> volume, then ingest.
        </p>
        <input
          type="file"
          accept="application/pdf,.pdf"
          disabled={busy}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          style={{ display: "block", marginBottom: "0.5rem" }}
        />
        {file ? (
          <p style={{ fontSize: "0.9rem", marginBottom: "0.5rem" }}>
            Using upload: <strong>{file.name}</strong>{" "}
            <button type="button" disabled={busy} onClick={() => setFile(null)}>
              Clear file (use JSON filename path instead)
            </button>
          </p>
        ) : null}
        <label>
          Filing filename (for JSON ingest path){" "}
          <input
            value={filingId}
            onChange={(e) => setFilingId(e.target.value)}
            disabled={busy}
            style={{ width: "min(100%, 22rem)" }}
          />
        </label>
        <div style={{ marginTop: "0.75rem" }}>
          <button type="button" disabled={busy} onClick={runIngest}>
            Run ingest
          </button>
        </div>
        {ingestMsg ? (
          <p style={{ color: "green", marginTop: "0.5rem" }}>{ingestMsg}</p>
        ) : null}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>2. Analyze</h2>
        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          Task{" "}
          <select
            value={task}
            disabled={busy}
            onChange={(e) => setTask(e.target.value as "summary" | "risks")}
          >
            <option value="summary">summary</option>
            <option value="risks">risks</option>
          </select>
        </label>
        <button type="button" disabled={busy} onClick={runAnalyze}>
          Run analysis
        </button>
      </section>

      {busy ? <p>Working…</p> : null}

      {error ? (
        <div
          role="alert"
          style={{
            color: "darkred",
            background: "#fee",
            padding: "0.75rem",
            marginBottom: "1rem",
            whiteSpace: "pre-wrap",
          }}
        >
          {error}
        </div>
      ) : null}

      <section>
        <h2>Retrieved evidence (top-k)</h2>
        {evidence.length === 0 ? (
          <p>—</p>
        ) : (
          <ol>
            {evidence.map((ev) => (
              <li key={ev.chunk_id} style={{ marginBottom: "1rem" }}>
                <strong>{ev.chunk_id}</strong>
                <pre
                  style={{
                    whiteSpace: "pre-wrap",
                    background: "#f4f4f4",
                    padding: "0.5rem",
                    fontSize: "0.85rem",
                  }}
                >
                  {ev.excerpt}
                </pre>
                <small>metadata: {JSON.stringify(ev.metadata)}</small>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2>Answer</h2>
        <pre
          style={{
            whiteSpace: "pre-wrap",
            background: "#f9f9f9",
            padding: "1rem",
            border: "1px solid #ccc",
            minHeight: "6rem",
          }}
        >
          {answer || "—"}
        </pre>
      </section>
    </main>
  );
}
