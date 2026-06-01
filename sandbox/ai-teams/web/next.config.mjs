const nextConfig = {
  // SSE は API サーバ(FastAPI:8000)へプロキシ。フロントは同一オリジンで /api を叩ける。
  async rewrites() {
    const apiBase = process.env.API_BASE || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${apiBase}/:path*` }];
  },
};

export default nextConfig;
