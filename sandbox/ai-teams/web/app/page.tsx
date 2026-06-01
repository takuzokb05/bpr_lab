"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { fetchPersonas, startSession } from "@/lib/sse";
import type { Persona, Turn } from "@/lib/types";
import { PersonaPicker } from "@/components/PersonaPicker";
import { Timeline } from "@/components/Timeline";
import { MinutesPanel } from "@/components/MinutesPanel";
import { Play, Square, AlertCircle } from "lucide-react";

type Status = "idle" | "running" | "done" | "error";

const DEFAULT_SELECTED = ["moderator", "logic", "idea", "empathy", "chair"];

export default function Home() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set(DEFAULT_SELECTED));
  const [topicInput, setTopicInput] = useState("");
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [streamingTurnId, setStreamingTurnId] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchPersonas()
      .then(setPersonas)
      .catch((e) => setError(String(e)));
  }, []);

  const looks = useMemo(() => {
    const m: Record<string, { accent: string; monogram: string }> = {};
    for (const p of personas) m[p.id] = { accent: p.accent, monogram: p.monogram };
    return m;
  }, [personas]);

  const synthesis = useMemo(
    () => turns.find((t) => t.phase === "synthesis") ?? null,
    [turns]
  );
  const summary = useMemo(
    () => turns.find((t) => t.phase === "summary") ?? null,
    [turns]
  );

  const running = status === "running";

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function stop() {
    abortRef.current?.abort();
    setStatus((s: Status) => (s === "running" ? "done" : s));
    setStreamingTurnId(null);
  }

  async function start() {
    const topic = topicInput.trim();
    if (!topic || selected.size === 0 || running) return;

    const ordered = personas.filter((p) => selected.has(p.id)).map((p) => p.id);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setActiveTopic(topic);
    setTurns([]);
    setError(null);
    setStatus("running");
    setStreamingTurnId(null);

    try {
      await startSession({
        topic,
        personaIds: ordered,
        mock: true, // APIキー未設定でも動くようデフォルトはモック。実LLMは false に。
        signal: ctrl.signal,
        onEvent: (e) => {
          if (e.type === "turn_start") {
            // 空の発言を1件追加し、以降の delta で本文を伸ばす（タイピング表示）。
            setTurns((prev) => [
              ...prev,
              {
                turn_id: e.turnId,
                speaker_id: e.speakerId,
                speaker_name: e.speakerName,
                content: "",
                phase: e.phase,
                round: e.round,
              },
            ]);
            setStreamingTurnId(e.turnId);
          } else if (e.type === "delta") {
            setTurns((prev) =>
              prev.map((t) =>
                t.turn_id === e.turnId ? { ...t, content: t.content + e.text } : t
              )
            );
          } else if (e.type === "turn_end") {
            setStreamingTurnId((cur) => (cur === e.turnId ? null : cur));
          } else if (e.type === "error") {
            setError(e.message);
            setStatus("error");
            setStreamingTurnId(null);
          } else if (e.type === "done") {
            setStatus("done");
            setStreamingTurnId(null);
          }
        },
      });
    } catch (err) {
      if (!ctrl.signal.aborted) {
        setError(String(err));
        setStatus("error");
      }
    }
  }

  return (
    <div className="flex h-screen flex-col">
      {/* ヘッダー */}
      <header className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-3">
        <h1 className="font-display text-base tracking-widest">AI COUNCIL</h1>
        <StatusBadge status={status} />
      </header>

      {/* 3レーン */}
      <div className="grid min-h-0 flex-1 grid-cols-[260px_1fr_320px]">
        {/* 左：編成 */}
        <aside className="overflow-y-auto border-r border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-5">
          <PersonaPicker
            personas={personas}
            selected={selected}
            onToggle={toggle}
            disabled={running}
          />
        </aside>

        {/* 中央：討論 */}
        <main className="flex min-h-0 flex-col">
          <div className="min-h-0 flex-1">
            <Timeline
              topic={activeTopic}
              turns={turns}
              streamingTurnId={streamingTurnId}
              looks={looks}
              status={status}
            />
          </div>

          {error && (
            <div className="mx-6 mb-2 flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          {/* 入力バー */}
          <div className="border-t border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-3">
            <div className="flex items-end gap-2">
              <textarea
                value={topicInput}
                onChange={(e) => setTopicInput(e.target.value)}
                onKeyDown={(e) => {
                  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") start();
                }}
                rows={1}
                placeholder="議題を入力（⌘/Ctrl+Enter で開始）"
                disabled={running}
                className="max-h-32 min-h-[40px] flex-1 resize-none rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2 text-sm outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
              />
              {running ? (
                <button
                  onClick={stop}
                  className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-4 py-2 text-sm hover:border-[var(--color-ink-muted)]"
                >
                  <Square size={14} /> 停止
                </button>
              ) : (
                <button
                  onClick={start}
                  disabled={!topicInput.trim() || selected.size === 0}
                  className="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
                >
                  <Play size={14} /> 討論を開始
                </button>
              )}
            </div>
          </div>
        </main>

        {/* 右：成果 */}
        <aside className="overflow-hidden border-l border-[var(--color-line)] bg-[var(--color-surface)]">
          <MinutesPanel summary={summary} synthesis={synthesis} status={status} />
        </aside>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: Status }) {
  const map: Record<Status, { label: string; color: string }> = {
    idle: { label: "待機中", color: "var(--color-ink-muted)" },
    running: { label: "進行中", color: "var(--color-accent)" },
    done: { label: "完了", color: "#3B6E5B" },
    error: { label: "エラー", color: "#b91c1c" },
  };
  const s = map[status];
  return (
    <span className="flex items-center gap-1.5 text-xs text-[var(--color-ink-muted)]">
      <span
        className={`inline-block h-2 w-2 rounded-full ${status === "running" ? "animate-pulse-soft" : ""}`}
        style={{ backgroundColor: s.color }}
      />
      {s.label}
    </span>
  );
}
