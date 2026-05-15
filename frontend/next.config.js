/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV !== 'production';

const nextConfig = {
  output: 'export',
  reactStrictMode: true,
  images: { unoptimized: true },
  trailingSlash: false,
  // Dev-only proxy to the FastAPI backend so /api/* hits :8000 without CORS.
  // Rewrites are stripped from the static export (warning suppressed by
  // gating on NODE_ENV).
  ...(isDev
    ? {
        async rewrites() {
          return [
            { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
          ];
        },
      }
    : {}),
};

module.exports = nextConfig;
