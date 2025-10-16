/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  output: 'standalone',
  env: {
    BACKEND_BASE_URL: process.env.BACKEND_BASE_URL || 'http://localhost:8000',
    PUBLIC_PORTAL_BASE_URL: process.env.PUBLIC_PORTAL_BASE_URL || 'http://localhost:3000',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.BACKEND_BASE_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
  images: {
    domains: ['localhost'],
    unoptimized: true,
  },
};

module.exports = nextConfig;
