import type { NextConfig } from "next";



const nextConfig: NextConfig = {
  compress:false,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_BASE_URL}/api/:path*`, // dynamic from env
      },
    ];
  },
};

export default nextConfig;
