// API（FastAPI）と共有する型。api/service.py の出力に対応する。

export type PersonaCategory =
  | "facilitation"
  | "chair"
  | "scribe"
  | "thinking"
  | "founders"
  | "philosophers";

export interface Persona {
  id: string;
  display_name: string;
  category: PersonaCategory;
  accent: string; // #RRGGBB
  monogram: string;
  tags: string[];
  speaks: boolean;
  model: string | null;
}

export interface Turn {
  turn_id: number; // ストリーミング/再接続でターンを一意に識別
  speaker_id: string;
  speaker_name: string;
  content: string; // ストリーミング中は delta で伸びていく
  phase: string;
  round: number;
  ts?: number; // サーバ採番の UNIX 秒（_append の time.time()）。再接続でも不変
}

// 主訴確認（intake）の Q&A。討論前に主訴を固め逸脱を防ぐ確認質問とその回答。
// 回答は任意（answer="" のままでもよい）。回答済みのものだけ /sessions に渡す。
export interface IntakeQA {
  question: string;
  answer: string;
}

// system_prompt 等を含むペルソナ詳細（GET /personas/{id}）。一覧の Persona は安全版。
export interface PersonaDetail extends Persona {
  system_prompt: string;
  temperature: number | null;
  avatar?: string; // 旧スキーマ互換（UI では使わない）
}

// プリセット（編成テンプレート）。builtin=true は読取専用。
export interface Preset {
  id: string;
  name: string;
  description?: string;
  persona_ids: string[];
  rounds_per_phase: number;
  red_team: boolean;
  red_team_id?: string | null;
  builtin: boolean;
}

// フェーズ名（API値）→ 報道トーンの表示ラベル
export const PHASE_LABELS: Record<string, string> = {
  opening: "オープニング",
  発散: "発散",
  批判: "批判",
  収束: "収束",
  summary: "要約",
  synthesis: "統合",
  human: "あなた",
  followup: "追い質問",
};

// 本編フェーズ（追い質問を拾える＝pull 対象）
export const MAIN_PHASES = ["発散", "批判", "収束"] as const;

// 追い質問を出せないフェーズ（opening/要約/統合の間は入力を無効化する）
export const FOLLOWUP_DISABLED_PHASES = ["opening", "summary", "synthesis"] as const;

/**
 * サーバ採番の ts（UNIX 秒）を日本時間の HH:mm にする。未定義なら空文字。
 * 再接続再生でも ts は不変なので、表示時刻がブレない。
 */
export function formatTurnTime(ts?: number): string {
  if (ts === undefined || ts === null) return "";
  return new Date(ts * 1000).toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// カテゴリ → 表示ラベル
export const CATEGORY_LABELS: Record<PersonaCategory, string> = {
  facilitation: "進行",
  chair: "統合",
  scribe: "記録",
  thinking: "思考",
  founders: "経営者",
  philosophers: "哲学者",
};
