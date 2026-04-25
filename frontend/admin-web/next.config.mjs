/** @type {import('next').NextConfig} */
//
// admin-web is mounted under `/admin` in production (host nginx
// forwards `/admin/...` to this container, while `/` goes to reader-web).
// `basePath` + `assetPrefix` make Next.js emit `/admin/_next/...` for
// static chunks so they route to this container correctly.
//
// In dev (npm run dev) we keep the empty basePath because the dev server
// runs standalone on :3000.
//
// Override at build time via NEXT_BASE_PATH env. Empty string disables.
const BASE_PATH =
  process.env.NEXT_BASE_PATH !== undefined
    ? process.env.NEXT_BASE_PATH
    : "/admin";

const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  basePath: BASE_PATH || undefined,
  assetPrefix: BASE_PATH || undefined,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
