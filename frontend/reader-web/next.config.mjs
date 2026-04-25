/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
  webpack: (config) => {
    // react-pdf / pdfjs-dist needs `canvas` only in node; alias to false
    // so webpack doesn't try to bundle it for the browser.
    config.resolve.alias = { ...(config.resolve.alias ?? {}), canvas: false };

    // pdf.worker.min.mjs uses top-level import/export — Terser refuses to
    // minify that and the build fails with "import/export cannot be used
    // outside of module code". Mark the worker as asset/resource so
    // webpack copies it untouched (we never reference it via webpack
    // anyway; PdfReader loads it from `/pdf.worker.min.mjs` in /public).
    config.module.rules.push({
      test: /pdf\.worker(?:\.min)?\.m?js$/i,
      type: "asset/resource",
      generator: { filename: "static/worker/[hash][ext][query]" },
    });
    return config;
  },
};

export default nextConfig;
