// API（FastAPI）と共有する型。api/service.py の出力に対応する。

export type PersonaCategory =
  | "facilitation"
  | "chair"
  | "scribe"
  | "thinking"
  | "founders"
  | "philosophers";

// 偉人同士の因縁（対立/盟友/師弟）。相手 id・関係種別・一言。ピッカーで相手をサジェストする。
export interface PersonaRelationship {
  to: string;
  type: "rival" | "ally" | "mentor" | "student";
  note?: string;
}

export interface Persona {
  id: string;
  display_name: string;
  category: PersonaCategory;
  description?: string; // ピッカーの1行ティーザー（「どんな人か」）。空/未定義なら非表示
  detail?: string; // 「詳細」展開で出す詳しい説明（偉人の背景＋持ち味 等）。空/未定義なら非表示
  accent: string; // #RRGGBB
  monogram: string;
  tags: string[];
  speaks: boolean;
  model: string | null;
  relationships?: PersonaRelationship[]; // 因縁（対立/盟友）。サーバ由来。custom は持たない
  custom?: boolean; // クライアント定義（自分のペルソナ）か。バッジ表示・送信判定に使う
}

// クライアント（ブラウザ）定義のカスタムペルソナ。localStorage が実体、サーバ非保存。
// category はパネリスト系のみ（構造役は自動固定なので対象外）。
export interface CustomPersona {
  id: string;
  display_name: string;
  category: "thinking" | "founders" | "philosophers";
  system_prompt: string;
  description?: string; // ピッカーの1行ティーザー（任意）
  detail?: string; // 「詳細」展開の詳しい説明（任意）
  tags?: string[];
}

// クライアント側のカテゴリ色（core/personas.py の CATEGORY_ACCENT と一致させる）。
const CUSTOM_CATEGORY_ACCENT: Record<string, string> = {
  thinking: "#5B7C8A",
  founders: "#8A6D3B",
  philosophers: "#6E5B8A",
};

// display_name から頭文字（モノグラム）を作る（core の monogram ロジックに準拠）。
export function customMonogram(name: string): string {
  const words = name.replace("　", " ").trim().split(/\s+/);
  if (words.length >= 2 && /^[A-Za-z]/.test(words[0]) && /^[A-Za-z]/.test(words[1])) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  const base = name.split("（")[0].split("(")[0].trim();
  return base.slice(0, 1) || "?";
}

// カスタムペルソナを画面表示用 Persona に変換（accent/monogram をクライアントで補う）。
export function customToPersona(cp: CustomPersona): Persona {
  return {
    id: cp.id,
    display_name: cp.display_name,
    category: cp.category,
    description: cp.description ?? "",
    detail: cp.detail ?? "",
    accent: CUSTOM_CATEGORY_ACCENT[cp.category] ?? "#5B7C8A",
    monogram: customMonogram(cp.display_name),
    tags: cp.tags ?? [],
    speaks: true,
    model: null,
    relationships: [],
    custom: true,
  };
}

export interface Turn {
  turn_id: number; // ストリーミング/再接続でターンを一意に識別
  speaker_id: string;
  speaker_name: string;
  content: string; // ストリーミング中は delta で伸びていく
  phase: string;
  round: number;
  ts?: number; // サーバ採番の UNIX 秒（_append の time.time()）。再接続でも不変
  query?: string; // 調査役の検索クエリ（research のみ。「『〇〇』を調べています…」表示用）
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
  bridge: "論点整理",
  批判: "批判",
  収束: "収束",
  closing: "クロージング",
  summary: "要約",
  synthesis: "統合",
  human: "あなた",
  followup: "追い質問",
  research: "調査",
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
