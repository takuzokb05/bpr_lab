// SSE クライアント。Step 2 の新プロトコル（start / turn_start / delta / turn_end /
// done / error、各 data に seq）を購読し、接続が切れたら GET …/stream?cursor=N で
// 自動再接続してバックログを再生 → ライブ継続する（設計 v2 Step 5）。
//
// 重要: Next の rewrite プロキシは SSE をバッファするため、API は apiUrl() で
// バックエンドへ直結する（プロキシ経由だと討論が一括表示になりライブ感が消える）。

import { apiUrl, apiHeaders } from "./config";
import type { IntakeQA } from "./types";

// 各イベントに ts（サーバ採番の UNIX 秒、_append の time.time()）を任意で載せる。
// 再接続再生でも同じ ts が来るので表示時刻がブレない（凍結契約: 時刻）。
export type StreamEvent =
  | { type: "start"; topic: string; sessionId: string; ts?: number }
  | {
      type: "turn_start";
      turnId: number;
      speakerId: string;
      speakerName: string;
      phase: string;
      round: number;
      ts?: number;
    }
  | { type: "delta"; turnId: number; text: string; ts?: number }
  | { type: "turn_end"; turnId: number; ts?: number }
  // floor-open（議場開放）: 本編フェーズの後、自動 synthesis せず入力待ちに入った合図。
  // フロントは追い質問入力＋「議事録を作る」「終了」を提示する（凍結契約: floor-open）。
  | { type: "paused"; phase?: string; ts?: number }
  | { type: "error"; message: string; ts?: number }
  | { type: "done"; ts?: number };

export interface StartSessionArgs {
  topic: string;
  personaIds: string[];
  roundsPerPhase?: number;
  redTeam?: boolean;
  redTeamId?: string | null;
  mock?: boolean;
  // 準備フェーズ（資料接地）。全ペルソナが共有する「資料・前提」。既定 "" で従来と完全同一。
  materials?: string;
  // 準備フェーズ（主訴確認）。回答済みの確認 Q&A。既定 [] で従来と完全同一。
  intake?: IntakeQA[];
  // 対話モード（議場開放）。Web は既定 true＝本編後に自動 synthesis せず一時停止して入力を待つ。
  interactive?: boolean;
  // Web 検索（調査役による事実調べ）。既定 false で従来と完全同一（body にも載らない）。
  // true のとき調査役が discussion 序盤と「要調査:」マーカーで検索し全員に共有する（コスト増）。
  research?: boolean;
  // 応答の長さプリセット（既定 standard）。トークン数ではなく質感で選ぶ。
  verbosity?: "brief" | "standard" | "deep";
  signal?: AbortSignal;
  onEvent: (e: StreamEvent) => void;
}

// 再接続をまたいで共有する読み取り状態。
interface PumpState {
  sessionId: string | null;
  lastSeq: number; // これまでに受け取った最大 seq（再接続カーソルの基準）
  terminal: boolean; // done / error を受け取ったか
}

/**
 * POST /api/sessions で討論を開始し、SSE を購読する。
 *
 * EventSource は POST 不可なので fetch + ReadableStream で自前パースする。
 * done/error 前にストリームが切れたら、最後に見た seq の次から自動再接続する
 * （プロデューサはバックグラウンドで完走しているので取りこぼさない）。
 */
export async function startSession({
  topic,
  personaIds,
  roundsPerPhase = 1,
  redTeam,
  redTeamId,
  mock = false,
  materials = "",
  intake = [],
  interactive = true,
  research = false,
  verbosity = "standard",
  signal,
  onEvent,
}: StartSessionArgs): Promise<void> {
  // GAP6: プリセットの設定（ラウンド数・Red Team）が無視されないよう必ず body に載せる。
  // interactive: Web は既定 true（本編後に floor-open で一時停止）。
  const body: Record<string, unknown> = {
    topic,
    persona_ids: personaIds,
    rounds_per_phase: roundsPerPhase,
    mock,
    interactive,
  };
  if (redTeam !== undefined) body.red_team = redTeam;
  if (redTeamId !== undefined && redTeamId !== null) body.red_team_id = redTeamId;
  // 準備フェーズ。後方互換: 空のときは body に載せない（従来の POST と完全同一）。
  if (materials.trim()) body.materials = materials;
  if (intake.length > 0) body.intake = intake;
  // Web 検索（調査役）。後方互換: false のときは body に載せない（従来の POST と完全同一）。
  if (research) body.research = research;
  // 応答の長さ。後方互換: standard（既定）のときは body に載せない。
  if (verbosity && verbosity !== "standard") body.verbosity = verbosity;

  const res = await fetch(apiUrl("/sessions"), {
    method: "POST",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok || !res.body) {
    onEvent({ type: "error", message: await errorDetail(res) });
    return;
  }

  const state: PumpState = { sessionId: null, lastSeq: -1, terminal: false };
  await pump(res, state, onEvent);

  // 再接続ループ: 正常終了でも abort でもなく切れた場合、続きを取りに行く。
  while (!state.terminal && !signal?.aborted && state.sessionId) {
    let r: Response;
    try {
      r = await fetch(
        apiUrl(`/sessions/${state.sessionId}/stream?cursor=${state.lastSeq + 1}`),
        { headers: apiHeaders(), signal }
      );
    } catch {
      break; // ネットワーク断など。これ以上は諦める（MVP の割り切り）。
    }
    if (!r.ok || !r.body) break;
    await pump(r, state, onEvent);
  }
}

/** 1レスポンスの本文を読み切り、SSE フレームを onEvent に流す（切断で return）。 */
async function pump(
  res: Response,
  state: PumpState,
  onEvent: (e: StreamEvent) => void
): Promise<void> {
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const frame = parseFrame(raw);
      if (!frame) continue;

      const { event, data } = frame;
      if (typeof data.seq === "number") {
        state.lastSeq = Math.max(state.lastSeq, data.seq);
      }
      const ev = toEvent(event, data, state);
      if (ev) onEvent(ev);
      if (event === "done" || event === "error") state.terminal = true;
    }
  }
}

interface Frame {
  event: string;
  data: Record<string, unknown>;
}

function parseFrame(raw: string): Frame | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  const dataStr = dataLines.join("\n");
  if (!dataStr) return { event, data: {} };
  try {
    return { event, data: JSON.parse(dataStr) as Record<string, unknown> };
  } catch {
    return null;
  }
}

function toEvent(
  event: string,
  d: Record<string, unknown>,
  state: PumpState
): StreamEvent | null {
  const ts = d.ts as number | undefined;
  switch (event) {
    case "start":
      state.sessionId = (d.session_id as string) ?? state.sessionId;
      return { type: "start", topic: d.topic as string, sessionId: state.sessionId!, ts };
    case "turn_start":
      return {
        type: "turn_start",
        turnId: d.turn_id as number,
        speakerId: d.speaker_id as string,
        speakerName: d.speaker_name as string,
        phase: d.phase as string,
        round: d.round as number,
        ts,
      };
    case "delta":
      return { type: "delta", turnId: d.turn_id as number, text: d.text as string, ts };
    case "turn_end":
      return { type: "turn_end", turnId: d.turn_id as number, ts };
    case "paused":
      // floor-open。lastSeq 更新は pump 側の既存ロジックに任せる（seq は _append 付与）。
      // terminal にはしない＝接続は保ったまま、ユーザー入力で turn_start が再開する。
      return { type: "paused", phase: d.phase as string | undefined, ts };
    case "error":
      return { type: "error", message: d.message as string, ts };
    case "done":
      return { type: "done", ts };
    default:
      return null;
  }
}

/** FastAPI の {detail:...}（文字列 or 422 配列）を人間向けメッセージにする。 */
export async function errorDetail(res: Response): Promise<string> {
  try {
    const j = await res.json();
    if (j?.detail) {
      return typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    }
  } catch {
    /* ignore */
  }
  return `HTTP ${res.status}`;
}

export async function fetchPersonas(): Promise<import("./types").Persona[]> {
  const res = await fetch(apiUrl("/personas"), { headers: apiHeaders() });
  if (!res.ok) throw new Error(`personas fetch failed: HTTP ${res.status}`);
  return res.json();
}

// -- 追い質問 ---------------------------------------------------------------
//
// 凍結契約: SSE には新イベント型を増やさない。追い質問は POST で投函するだけで、
// 結果は既存の turn_start→delta→turn_end として返ってくる（人間ターン＋司会再提示＋
// パネリスト1周）。成功は 202 {"queued":true}。
export async function sendFollowup(sessionId: string, text: string): Promise<void> {
  const res = await fetch(apiUrl(`/sessions/${sessionId}/messages`), {
    method: "POST",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ kind: "followup", text, target: null }),
  });
  // 2xx を成功とみなす（202 固定に依存しない＝プロキシが 200/204 にしても壊れない）。
  if (!res.ok) {
    throw new Error(await errorDetail(res));
  }
}

// -- 議場開放（floor-open）の締め／終了 -------------------------------------
//
// 凍結契約: floor-open 中の3アクションのうち「締める」「終了」は body なしの POST。
// 締める(close)＝議事録(synthesis)を1回生成して再び floor-open に戻る。
// 終了(finish)＝floor-open ループを抜けて done。どちらも結果は既存の
// turn_start→delta→turn_end / done として SSE で返る（新イベントは増やさない）。
export async function closeSession(sessionId: string): Promise<void> {
  const res = await fetch(apiUrl(`/sessions/${sessionId}/close`), {
    method: "POST",
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
}

export async function finishSession(sessionId: string): Promise<void> {
  const res = await fetch(apiUrl(`/sessions/${sessionId}/finish`), {
    method: "POST",
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
}

// -- 停止（協調キャンセル） -------------------------------------------------
//
// 討論はバックグラウンドで完走する設計なので、停止は DELETE で明示的に伝える
// （実 LLM の発注を次のターン前に止めてコストを抑える）。404/既終了でも実害なく握る。
export async function cancelSession(sessionId: string): Promise<void> {
  try {
    await fetch(apiUrl(`/sessions/${sessionId}`), {
      method: "DELETE",
      headers: apiHeaders(),
    });
  } catch {
    /* ネットワーク断などは無視（表示側はすでに停止扱い） */
  }
}

// -- ヘルス（LLM 状態） -----------------------------------------------------
export interface Health {
  status: string;
  llm: "anthropic" | "mock" | "byok";
  api_key_set: boolean;
  // BYOK（各自が自分の API キーを持参）モードか。true なら実 LLM は各自のキーが必要。
  byok?: boolean;
  // 対応プロバイダ（anthropic/openai/google）。Web 検索は research_provider のみ対応。
  providers?: string[];
  research_provider?: string;
  // 編成 CRUD が書き込み禁止か（共有インスタンス）。true なら「管理」UI を隠す。
  readonly?: boolean;
}

export async function fetchHealth(): Promise<Health> {
  const res = await fetch(apiUrl("/health"), { headers: apiHeaders() });
  if (!res.ok) throw new Error(`health fetch failed: HTTP ${res.status}`);
  return res.json();
}

// -- 主訴確認（intake） -----------------------------------------------------
//
// 準備フェーズ: 討論の手前で主訴を固め逸脱を防ぐ確認質問を 2〜4 個もらう。
// POST /intake {topic, materials?, mock} → 200 {questions: string[]}。
// mock or キー未設定ならサーバが LLM を呼ばず定型質問を返す（安価）。直結で取得する。
// mock は討論の設定に追従させる＝mock モードで主訴確認だけ勝手に課金しないようにする。
export async function fetchIntake(
  topic: string,
  materials?: string,
  mock = false
): Promise<string[]> {
  const body: Record<string, unknown> = { topic, mock };
  if (materials && materials.trim()) body.materials = materials;
  const res = await fetch(apiUrl("/intake"), {
    method: "POST",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  const j = (await res.json()) as { questions?: unknown };
  // 防御的に整形: questions が配列でない / 空文字混入でも壊れない。
  return Array.isArray(j.questions)
    ? j.questions.filter((q): q is string => typeof q === "string" && q.trim() !== "")
    : [];
}
