// API のベース URL。
//
// Next.js の rewrite プロキシ（next.config.mjs の /api/:path*）は SSE レスポンスを
// バッファしてしまい、討論が「終わってから一括表示」になる（＝ライブ感が消える）。
// 実測: バックエンド直結は逐次配信、プロキシ経由は塊で遅延配信。
// そこでストリーミングを含む全 API をプロキシを通さずバックエンドへ直結する。
//
// 既定はローカルの FastAPI(:8000)。別ホスト/本番は NEXT_PUBLIC_API_BASE で上書きする
// （例: NEXT_PUBLIC_API_BASE=https://api.example.com）。CORS はバックエンド側で許可済み。
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}
