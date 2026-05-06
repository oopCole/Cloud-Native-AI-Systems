import type { NextRequest } from "next/server";

/**
 * Same-origin proxy:
 * browser -> /car-api/* -> backend API
 * Keeps frontend/backend decoupled and avoids CORS issues in local/dev environments.
 */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const backendBase =
  process.env.BACKEND_INTERNAL_URL?.replace(/\/$/, "") || "http://127.0.0.1:8001";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-connection",
  "transfer-encoding",
  "upgrade",
  "host",
]);

function filterHeaders(incoming: Headers): Headers {
  const out = new Headers();
  incoming.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      out.append(key, value);
    }
  });
  return out;
}

async function proxy(req: NextRequest, segments: string[]): Promise<Response> {
  const suffix = segments.length ? `/${segments.join("/")}` : "";
  const targetUrl = `${backendBase}${suffix}${req.nextUrl.search}`;

  const init: RequestInit & { duplex?: "half" } = {
    method: req.method,
    headers: filterHeaders(req.headers),
    redirect: "manual",
  };

  if (!["GET", "HEAD", "OPTIONS"].includes(req.method) && req.body) {
    init.body = req.body;
    init.duplex = "half";
  }

  const upstream = await fetch(targetUrl, init);
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: filterHeaders(upstream.headers),
  });
}

type Ctx = { params: Promise<{ path?: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, path);
}

export async function HEAD(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, path);
}

export async function POST(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, path);
}

export async function PUT(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, path);
}

export async function PATCH(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, path);
}

export async function DELETE(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, path);
}

export async function OPTIONS(req: NextRequest, ctx: Ctx) {
  const { path = [] } = await ctx.params;
  return proxy(req, path);
}
