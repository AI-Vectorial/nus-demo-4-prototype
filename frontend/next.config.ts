import type { NextConfig } from "next";

const config: NextConfig = {
  // Railway runs `next start`; standalone keeps the deployed image small.
  output: "standalone",
  reactStrictMode: true,
};

export default config;
