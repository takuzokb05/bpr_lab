// SSE クライアント。Step 2 の新プロトコル（start / turn_start / delta / turn_end /
// done / error、各 data に seq）を購読し、接続が切れたら GET …/stream?cursor=N で
// 自動再接続してバックログを再生 → ライブ継続する（設計 v2 Step 5）。

export type StreamEvent =
  | { type: "start"; topic: string; sessionId: string }
  | {
      type: "turn_start";
      turnId: number;
      speakerId: string;
      speakerName: string;
      phase: string;
      round: number;
    }
  | { type: "delta"; turnId: number; text: string }
  | { type: "turn_end"; turnId: number }
  | { type: "error"; message: string }
  | { type: "done" };

export interface StartSessionArgs {
  topic: string;
  personaIds: string[];
  roundsPerPhase?: number;
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
  mock = false,
  signal,
  onEvent,
}: StartSessionArgs): Promise<void> {
  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      topic,
      persona_ids: personaIds,
      rounds_per_phase: roundsPerPhase,
      mock,
    }),
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
  switch (event) {
    case "start":
      state.sessionId = (d.session_id as string) ?? state.sessionId;
      return { type: "start", topic: d.topic as string, sessionId: state.sessionId! };
    case "turn_start":
      return {
        type: "turn_start",
        turnId: d.turn_id as number,
        speakerId: d.speaker_id as string,
        speakerName: d.speaker_name as string,
        phase: d.phase as string,
        round: d.round as number,
      };
    case "delta":
      return { type: "delta", turnId: d.turn_id as number, text: d.text as string };
    case "turn_end":
      return { type: "turn_end", turnId: d.turn_id as number };
    case "error":
      return { type: "error", message: d.message as string };
    case "done":
      return { type: "done" };
    default:
      return null;
  }
}

async function errorDetail(res: Response): Promise<string> {
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
