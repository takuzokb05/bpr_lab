import type { Turn } from "./types";

export type StreamEvent =
  | { type: "start"; topic: string }
  | { type: "turn"; turn: Turn }
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

/**
 * POST /api/sessions を叩き、SSE を逐次パースして onEvent に流す。
 *
 * EventSource は POST/ボディを送れないため fetch + ReadableStream で自前パースする。
 * core/orchestrator.run() の yield が、ここで1発言ずつ届く（v2 の「途中経過が
 * 見えない」を構造的に解消）。
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
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* ignore */
    }
    onEvent({ type: "error", message: detail });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE はイベントを空行(\n\n)で区切る
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const parsed = parseEvent(raw);
      if (parsed) onEvent(parsed);
    }
  }
}

function parseEvent(raw: string): StreamEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  const dataStr = dataLines.join("\n");
  let data: unknown = {};
  if (dataStr) {
    try {
      data = JSON.parse(dataStr);
    } catch {
      return null;
    }
  }

  switch (event) {
    case "start":
      return { type: "start", topic: (data as { topic: string }).topic };
    case "turn":
      return { type: "turn", turn: data as Turn };
    case "error":
      return { type: "error", message: (data as { message: string }).message };
    case "done":
      return { type: "done" };
    default:
      return null;
  }
}

export async function fetchPersonas(): Promise<import("./types").Persona[]> {
  const res = await fetch("/api/personas");
  if (!res.ok) throw new Error(`personas fetch failed: HTTP ${res.status}`);
  return res.json();
}
