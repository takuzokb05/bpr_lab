// API のベース URL。
//
// Next.js の rewrite プロキシ（next.config.mjs の /api/:path*）は SSE レスポンスを
// バッファしてしまい、討論が「終わってから一括表示」になる（＝ライブ感が消える）。
// 実測: バックエンド直結は逐次配信、プロキシ経由は塊で遅延配信。
// そこでストリーミングを含む全 API をプロキシを通さずバックエンドへ直結する。
//
// 既定はローカルの FastAPI(:8000)。別ホスト/本番は NEXT_PUBLIC_API_BASE で上書きする
// （例: NEXT_PUBLIC_API_BASE=https://api.example.com）。CORS はバックエンド側で許可済み。
// 未設定(undefined) → ローカル開発の :8000。明示的に "" を渡すと相対パス＝同一オリジン
// （uvicorn が静的フロントを同居配信する本番構成。?? なので空文字はそのまま採用される）。
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

// -- BYOK（各自の Anthropic API キー） --------------------------------------
// キーは **このブラウザの localStorage にのみ**保存し、サーバには保存しない。
// 各リクエストの X-Anthropic-Key ヘッダで送り、サーバはそのキーで実 LLM を呼ぶ
// （セッション中のメモリ保持のみ・ログ/ディスクに残さない）。共有/公開時に
// 「サーバ所有者のキーが他人に使われる」事故を防ぐための仕組み。
const USER_KEY_STORAGE = "aiteams_llm_key";
const PROVIDER_STORAGE = "aiteams_llm_provider";

// 対応プロバイダ。各自は **1社のキーだけ**入れればよい（単一キー）。Web 検索は anthropic のみ。
export type LlmProvider = "anthropic" | "openai" | "google";
export const LLM_PROVIDERS: LlmProvider[] = ["anthropic", "openai", "google"];

export function getProvider(): LlmProvider {
  if (typeof window === "undefined") return "anthropic";
  try {
    const v = window.localStorage.getItem(PROVIDER_STORAGE);
    return (LLM_PROVIDERS as string[]).includes(v ?? "")
      ? (v as LlmProvider)
      : "anthropic";
  } catch {
    return "anthropic";
  }
}

export function setProvider(provider: LlmProvider): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(PROVIDER_STORAGE, provider);
  } catch {
    /* noop */
  }
}

// 応答の長さプリセット（トークン数ではなく質感で選ぶ）。
const VERBOSITY_STORAGE = "aiteams_verbosity";
export type Verbosity = "brief" | "standard" | "deep";
export const VERBOSITIES: Verbosity[] = ["brief", "standard", "deep"];

export function getVerbosity(): Verbosity {
  if (typeof window === "undefined") return "standard";
  try {
    const v = window.localStorage.getItem(VERBOSITY_STORAGE);
    return (VERBOSITIES as string[]).includes(v ?? "") ? (v as Verbosity) : "standard";
  } catch {
    return "standard";
  }
}

export function setVerbosity(v: Verbosity): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(VERBOSITY_STORAGE, v);
  } catch {
    /* noop */
  }
}

export function getUserKey(): string {
  if (typeof window === "undefined") return ""; // SSR / static export 時は空
  try {
    return window.localStorage.getItem(USER_KEY_STORAGE) ?? "";
  } catch {
    return "";
  }
}

export function setUserKey(key: string): void {
  if (typeof window === "undefined") return;
  try {
    const v = key.trim();
    if (v) window.localStorage.setItem(USER_KEY_STORAGE, v);
    else window.localStorage.removeItem(USER_KEY_STORAGE);
  } catch {
    /* localStorage 不可（プライベートモード等）でも本体は動く */
  }
}

// 最小認証（デプロイ準備）。本番ビルドに NEXT_PUBLIC_API_TOKEN を設定すると
// 全 fetch に Authorization: Bearer <token> を載せる。未設定なら何も足さない。
// さらに BYOK のキーがあれば X-LLM-Provider + X-LLM-Key を載せる（実 LLM 用）。
// extra（Content-Type 等）とマージして返す。
export function apiHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = { ...(extra ?? {}) };
  const token = process.env.NEXT_PUBLIC_API_TOKEN;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const userKey = getUserKey();
  if (userKey) {
    headers["X-LLM-Key"] = userKey;
    headers["X-LLM-Provider"] = getProvider();
  }
  return headers;
}
