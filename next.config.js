const nextConfig = {
  images: {
    unoptimized: true,
  },
  // Enable standalone output for Docker
  output: "standalone",
  webpack(config, { dev }) {
    if (dev) {
      // Reduce CPU/memory from file watching
      config.watchOptions = {
        poll: 2000, // check every 2 seconds
        aggregateTimeout: 300, // wait before rebuilding
        ignored: ["**/node_modules"],
      };
    }
    return config;
  },
  onDemandEntries: {
    maxInactiveAge: 10000,
    pagesBufferLength: 2,
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          // Only this site may frame its pages (was: any site, which allows
          // clickjacking-style overlays).
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "Content-Security-Policy", value: "frame-ancestors 'self';" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          // No Access-Control-Allow-* headers: only this site's own pages
          // call /api, so browsers need no cross-origin permission.
        ],
      },
    ];
  },
};

module.exports = nextConfig;
