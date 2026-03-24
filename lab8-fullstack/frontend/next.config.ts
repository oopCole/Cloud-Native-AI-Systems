import type { NextConfig } from "next";

/**
 * `/lab8-api/*` is proxied by `app/lab8-api/[[...path]]/route.ts` so file uploads work.
 * Set BACKEND_INTERNAL_URL (Docker: http://backend:8000; local dev: http://127.0.0.1:8000).
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
