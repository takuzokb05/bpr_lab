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
}

// フェーズ名（API値）→ 報道トーンの表示ラベル
export const PHASE_LABELS: Record<string, string> = {
  opening: "オープニング",
  発散: "発散",
  批判: "批判",
  収束: "収束",
  summary: "要約",
  synthesis: "統合",
};

// カテゴリ → 表示ラベル
export const CATEGORY_LABELS: Record<PersonaCategory, string> = {
  facilitation: "進行",
  chair: "統合",
  scribe: "記録",
  thinking: "思考",
  founders: "経営者",
  philosophers: "哲学者",
};
