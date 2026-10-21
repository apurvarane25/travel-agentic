import type { NextConfig } from "next";

// Server-side only (no NEXT_PUBLIC_ prefix), so the backend URL never reaches the browser bundle.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // The browser calls same-origin /api/*; Next forwards it to FastAPI. No CORS needed.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
  },
  experimental: {
    // The rewrite proxy gives up after 30 s by default. Agent requests with retries can take longer.
    proxyTimeout: 60_000,
  },
};

export default nextConfig;
