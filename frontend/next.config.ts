import type { NextConfig } from "next";

const config: NextConfig = {
  // Railway runs `next start`; standalone keeps the deployed image small.
  output: "standalone",
  reactStrictMode: true,

  // Development only. In a browser-based Codespace the page can reach port
  // 3000 but not the API's port, so the dev server forwards /api/* to the API
  // inside the Codespace. Production never uses this: there the page calls
  // API_URL directly (app/page.tsx).
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    const api = process.env.API_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${api}/:path*` }];
  },
};

export default config;
