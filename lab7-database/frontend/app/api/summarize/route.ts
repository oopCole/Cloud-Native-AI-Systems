import { NextRequest } from "next/server";

const BACKEND_BASE_URL =
  process.env.BACKEND_BASE_URL ?? "http://localhost:8000";
const DEV_JWT_TOKEN = process.env.DEV_JWT_TOKEN ?? "dev-token";

export async function POST(request: NextRequest) {
  let prompt: string;
  try {
    const body = await request.json();
    prompt =
      typeof body?.prompt === "string" ? body.prompt : String(body?.prompt ?? "");
  } catch {
    return new Response("Bad request: invalid JSON", { status: 400 });
  }

  const trimmed = prompt.trim();
  if (!trimmed) {
    return new Response("Bad request: prompt is required", { status: 400 });
  }

  const url = `${BACKEND_BASE_URL.replace(/\/$/, "")}/summarize`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${DEV_JWT_TOKEN}`,
    },
    body: JSON.stringify({ text: trimmed, max_length: 100 }),
  });

  if (!res.ok) {
    const text = await res.text();
    return new Response(
      text || `Backend error: ${res.status} ${res.statusText}`,
      { status: res.status }
    );
  }

  const data = (await res.json()) as { summary?: string };
  const summary =
    typeof data?.summary === "string" ? data.summary : String(data?.summary ?? "");

  return new Response(summary, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
