"use client";

import { type Turn } from "@/lib/types";
import { Avatar } from "./Avatar";
import { NamePlate } from "./NamePlate";
import { useEffect, useRef } from "react";

interface PersonaLook {
  accent: string;
  monogram: string;
}

export function Timeline({
  topic,
  turns,
  streamingTurnId,
  looks,
  status,
}: {
  topic: string | null;
  turns: Turn[];
  streamingTurnId: number | null;
  looks: Record<string, PersonaLook>;
  status: "idle" | "running" | "done" | "error";
}) {
  const endRef = useRef<HTMLDivElement>(null);

  // 末尾ターンの本文が伸びるたびに追従スクロールする
  const lastContent = turns.length ? turns[turns.length - 1].content : "";

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, lastContent, streamingTurnId]);

  if (!topic) {
    return (
      <div className="flex h-full items-center justify-center px-8 text-center">
        <p className="max-w-sm text-sm leading-relaxed text-[var(--color-ink-muted)]">
          左で参加者を編成し、下に議題を入力して討論を始めてください。
        </p>
      </div>
    );
  }

  // 議長の要約(summary)・統合(synthesis)はタイムラインから除外し、右の成果パネルに回す。
  // 人間ターン(human)・追い質問の再提示(followup)は本編として残す。
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
        {visible.map((t) => {
          const isStreaming = t.turn_id === streamingTurnId;

          // 人間ターン: 右寄せ・アクセント弱背景で「あなた」の発言として描く。
          // turn_id<0 は楽観的エコー（未確定）→ pending microcopy を添える。
          if (t.phase === "human") {
            const pending = t.turn_id < 0;
            return (
              <article
                key={t.turn_id}
                className="animate-turn-in flex flex-row-reverse gap-3"
              >
                <Avatar monogram="あ" accent="var(--color-ink-muted)" size={36} />
                <div className="min-w-0 flex-1">
                  <NamePlate name="あなた" phase={t.phase} ts={t.ts} />
                  <div className="mt-1 rounded-md bg-[var(--color-accent-weak)] px-3 py-2">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--color-ink)]">
                      {t.content}
                    </p>
                  </div>
                  {pending && (
                    <p className="mt-1 text-[11px] text-[var(--color-ink-muted)]">
                      次の発言から反映します
                    </p>
                  )}
                </div>
              </article>
            );
          }

          const look = looks[t.speaker_id] ?? { accent: "#5B7C8A", monogram: "?" };
          return (
            <article key={t.turn_id} className="animate-turn-in flex gap-3">
              <Avatar monogram={look.monogram} accent={look.accent} size={36} />
              <div className="min-w-0 flex-1">
                <NamePlate name={t.speaker_name} phase={t.phase} ts={t.ts} />
                {t.phase === "followup" && (
                  <span className="mt-1 inline-block text-[10px] font-medium uppercase tracking-wider text-[var(--color-accent)]">
                    追い質問
                  </span>
                )}
                <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-[var(--color-ink)]">
                  {/* 本文が空のまま発言中なら「考え中」、delta が来たら本文＋点滅キャレット */}
                  {t.content === "" && isStreaming ? (
                    <span className="text-[var(--color-ink-muted)]">考えています…</span>
                  ) : (
                    <>
                      {t.content}
                      {isStreaming && (
                        <span className="animate-pulse-soft ml-0.5 inline-block align-middle">
                          ▍
                        </span>
                      )}
                    </>
                  )}
                </p>
              </div>
            </article>
          );
        })}
      </div>
      <div ref={endRef} />
    </div>
  );
}
