// 静的書き出し（static export）。`next build` で out/ に純粋な静的ファイルを生成し、
// uvicorn(FastAPI) が同一オリジンで配信する（Node 常駐不要・低RAM・CORS不要）。
// API は apiUrl()（NEXT_PUBLIC_API_BASE）で直接バックエンドへ。rewrites は static export では
// 使えず、かつ apiUrl 直結で不要なので置かない。
const nextConfig = {
  output: "export",
  images: { unoptimized: true }, // static export では画像最適化サーバが無いため
};

export default nextConfig;
