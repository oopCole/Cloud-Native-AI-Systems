import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const backend = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8001";
    return [
      {
        source: "/car-api/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
};

export default nextConfig;
