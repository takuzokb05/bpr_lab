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

// 対応プロバイダ。anthropic/openai/google は BYOK（各自1社のキー）。local は内製（自前ホスト/開源API）で
// キー不要（サーバ設定）＝BYOK のキー選択 UI には出さない（force_local で server 側が固定する）。
export type LlmProvider = "anthropic" | "openai" | "google" | "local";
// BYOK のキー入力で選べるプロバイダ（local は鍵不要なので含めない）。
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

// 自分のペルソナ（クライアント定義・localStorage が実体・サーバ非保存）。
import type { CustomPersona, Turn } from "./types";

// -- 討論履歴（クライアント保存・サーバ非依存） ------------------------------
// 討論はサーバのメモリ常駐で、再起動や TTL で消える。見返し／再開できるよう、
// transcript を **このブラウザの localStorage** に保存する（BYOK と同じ思想）。
const HISTORY_STORAGE = "aiteams_history";
const HISTORY_MAX = 20; // localStorage 肥大を避ける（古いものから捨てる）

export interface HistoryEntry {
  id: string; // = サーバの session_id
  topic: string;
  startedAt: number; // UNIX ms（最初に保存した時刻）
  updatedAt: number;
  status: string; // running | paused | done | error
  turns: Turn[];
}

export function getHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(HISTORY_STORAGE);
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

// id で upsert。startedAt は既存を温存し、updatedAt 降順（最近が先頭）で HISTORY_MAX 件に丸める。
export function saveHistoryEntry(
  entry: Omit<HistoryEntry, "startedAt" | "updatedAt"> & { startedAt?: number }
): void {
  if (typeof window === "undefined") return;
  if (!entry.id || !entry.topic) return;
  try {
    const now = Date.now();
    const list = getHistory();
    const existing = list.find((e) => e.id === entry.id);
    // 縮小上書き防止: 再接続の cursor=0 replay 中は turns が増えながら何度も保存される。
    // 非終端(running/paused 等)で既存より短い内容が来たら、途中切断による恒久縮小を避けて既存 turns を温存する。
    const isTerminal = entry.status === "done" || entry.status === "error";
    const shrinks =
      !!existing &&
      Array.isArray(entry.turns) &&
      entry.turns.length < existing.turns.length;
    const turns = !isTerminal && shrinks ? existing!.turns : entry.turns;
    const merged: HistoryEntry = {
      id: entry.id,
      topic: entry.topic,
      status: entry.status,
      turns,
      startedAt: existing?.startedAt ?? entry.startedAt ?? now,
      updatedAt: now,
    };
    const rest = list.filter((e) => e.id !== entry.id);
    const next = [merged, ...rest]
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, HISTORY_MAX);
    window.localStorage.setItem(HISTORY_STORAGE, JSON.stringify(next));
  } catch {
    /* 失敗（容量超過等）は無視。本体は動く */
  }
}

export function deleteHistoryEntry(id: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(
      HISTORY_STORAGE,
      JSON.stringify(getHistory().filter((e) => e.id !== id))
    );
  } catch {
    /* noop */
  }
}

const CUSTOM_PERSONAS_STORAGE = "aiteams_custom_personas";
const VALID_CUSTOM_CATS = ["thinking", "founders", "philosophers"];

function isValidCustom(x: unknown): x is CustomPersona {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return (
    typeof o.id === "string" &&
    /^[a-z0-9_-]+$/.test(o.id) &&
    typeof o.display_name === "string" &&
    o.display_name.trim().length > 0 &&
    typeof o.system_prompt === "string" &&
    o.system_prompt.trim().length > 0 &&
    typeof o.category === "string" &&
    VALID_CUSTOM_CATS.includes(o.category)
  );
}

export function getCustomPersonas(): CustomPersona[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(CUSTOM_PERSONAS_STORAGE);
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr.filter(isValidCustom) : [];
  } catch {
    return [];
  }
}

export function setCustomPersonas(list: CustomPersona[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(
      CUSTOM_PERSONAS_STORAGE,
      JSON.stringify(list.filter(isValidCustom))
    );
  } catch {
    /* localStorage 不可でも本体は動く */
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

// 討論モード（エンジン・プリセット）。preset id を localStorage に保存（local 経路でのみ使う）。
// 既定は health.default_preset（無ければ "standard"）。中身(model/長さ)はサーバが解決する。
const MODE_STORAGE = "aiteams_mode";

export function getMode(fallback = "standard"): string {
  if (typeof window === "undefined") return fallback;
  try {
    return window.localStorage.getItem(MODE_STORAGE) ?? fallback;
  } catch {
    return fallback;
  }
}

export function setMode(id: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(MODE_STORAGE, id);
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
