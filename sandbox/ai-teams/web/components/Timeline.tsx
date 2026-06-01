"use client";

import { PHASE_LABELS, type Turn } from "@/lib/types";
import { Avatar } from "./Avatar";
import { useEffect, useRef } from "react";

interface PersonaLook {
  accent: string;
  monogram: string;
}

export function Timeline({
  topic,
  turns,
  streamingSpeakerId,
  looks,
  status,
}: {
  topic: string | null;
  turns: Turn[];
  streamingSpeakerId: string | null;
  looks: Record<string, PersonaLook>;
  status: "idle" | "running" | "done" | "error";
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, streamingSpeakerId]);

  if (!topic) {
    return (
      <div className="flex h-full items-center justify-center px-8 text-center">
        <p className="max-w-sm text-sm leading-relaxed text-[var(--color-ink-muted)]">
          左で参加者を編成し、下に議題を入力して討論を始めてください。
        </p>
      </div>
    );
  }

  // 議長の要約(summary)・統合(synthesis)はタイムラインから除外し、右の成果パネルに回す
  const visible = turns.filter((t) => t.phase !== "synthesis" && t.phase !== "summary");

  return (
    <div className="flex h-full flex-col overflow-y-auto px-6 py-5">
      <div className="mb-5 border-b border-[var(--color-line)] pb-4">
        <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          議題
        </p>
        <h2 className="font-display mt-1 text-lg leading-snug">{topic}</h2>
      </div>

      <div className="flex flex-col gap-5">
        {visible.map((t, i) => {
          const look = looks[t.speaker_id] ?? { accent: "#5B7C8A", monogram: "?" };
          return (
            <article key={i} className="animate-turn-in flex gap-3">
              <Avatar monogram={look.monogram} accent={look.accent} size={36} />
              <div className="min-w-0 flex-1">
                <header className="flex items-baseline gap-2">
                  <span className="text-sm font-medium">{t.speaker_name}</span>
                  <span className="text-[11px] text-[var(--color-ink-muted)]">
                    {PHASE_LABELS[t.phase] ?? t.phase}
                  </span>
                </header>
                <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-[var(--color-ink)]">
                  {t.content}
                </p>
              </div>
            </article>
          );
        })}

        {status === "running" && streamingSpeakerId && (
          <div className="flex items-center gap-3 pl-12 text-xs text-[var(--color-ink-muted)]">
            <span className="animate-pulse-soft">
              {looks[streamingSpeakerId]?.monogram ?? ""} が発言中…
            </span>
          </div>
        )}
      </div>
      <div ref={endRef} />
    </div>
  );
}
