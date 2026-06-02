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

// 最小認証（デプロイ準備）。本番ビルドに NEXT_PUBLIC_API_TOKEN を設定すると
// 全 fetch に Authorization: Bearer <token> を載せる。未設定なら何も足さず
// 従来と同一ヘッダ（後方互換: ローカル開発・テストはこの経路で無改修動作）。
// extra（Content-Type 等）とマージして返す。
export function apiHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = { ...(extra ?? {}) };
  const token = process.env.NEXT_PUBLIC_API_TOKEN;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}
