// SSE クライアント。Step 2 の新プロトコル（start / turn_start / delta / turn_end /
// done / error、各 data に seq）を購読し、接続が切れたら GET …/stream?cursor=N で
// 自動再接続してバックログを再生 → ライブ継続する（設計 v2 Step 5）。

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
  | { type: "error"; message: string; ts?: number }
  | { type: "done"; ts?: number };

export interface StartSessionArgs {
  topic: string;
  personaIds: string[];
  roundsPerPhase?: number;
  redTeam?: boolean;
  redTeamId?: string | null;
  mock?: boolean;
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
  signal,
  onEvent,
}: StartSessionArgs): Promise<void> {
  // GAP6: プリセットの設定（ラウンド数・Red Team）が無視されないよう必ず body に載せる。
  const body: Record<string, unknown> = {
    topic,
    persona_ids: personaIds,
    rounds_per_phase: roundsPerPhase,
    mock,
  };
  if (redTeam !== undefined) body.red_team = redTeam;
  if (redTeamId !== undefined && redTeamId !== null) body.red_team_id = redTeamId;

  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
        `/api/sessions/${state.sessionId}/stream?cursor=${state.lastSeq + 1}`,
        { signal }
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
  const res = await fetch("/api/personas");
  if (!res.ok) throw new Error(`personas fetch failed: HTTP ${res.status}`);
  return res.json();
}

// -- 追い質問 ---------------------------------------------------------------
//
// 凍結契約: SSE には新イベント型を増やさない。追い質問は POST で投函するだけで、
// 結果は既存の turn_start→delta→turn_end として返ってくる（人間ターン＋司会再提示＋
// パネリスト1周）。成功は 202 {"queued":true}。
export async function sendFollowup(sessionId: string, text: string): Promise<void> {
  const res = await fetch(`/api/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind: "followup", text, target: null }),
  });
  // 2xx を成功とみなす（202 固定に依存しない＝プロキシが 200/204 にしても壊れない）。
  if (!res.ok) {
    throw new Error(await errorDetail(res));
  }
}

// -- 停止（協調キャンセル） -------------------------------------------------
//
// 討論はバックグラウンドで完走する設計なので、停止は DELETE で明示的に伝える
// （実 LLM の発注を次のターン前に止めてコストを抑える）。404/既終了でも実害なく握る。
export async function cancelSession(sessionId: string): Promise<void> {
  try {
    await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
  } catch {
    /* ネットワーク断などは無視（表示側はすでに停止扱い） */
  }
}

// -- ヘルス（LLM 状態） -----------------------------------------------------
export interface Health {
  status: string;
  llm: "anthropic" | "mock";
  api_key_set: boolean;
}

export async function fetchHealth(): Promise<Health> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`health fetch failed: HTTP ${res.status}`);
  return res.json();
}
