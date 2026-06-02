"use client";

import { type Turn, formatTurnTime } from "@/lib/types";
import { Avatar } from "./Avatar";
import { NamePlate } from "./NamePlate";
import { Markdown } from "./Markdown";
import { Search, Globe, Users } from "lucide-react";
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
  status: "idle" | "running" | "paused" | "done" | "error";
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
        <h2 className="font-display mt-1 text-lg leading-snug [overflow-wrap:anywhere]">{topic}</h2>
      </div>

      <div className="flex flex-col gap-5">
        {/* 最初の発言が来るまでの「生きてる感」。実LLMは初回トークンまで数秒かかる。 */}
        {status === "running" && visible.length === 0 && (
          <div className="flex items-center gap-2 text-sm text-[var(--color-ink-muted)]">
            <span className="animate-pulse-soft inline-block h-2 w-2 rounded-full bg-[var(--color-accent)]" />
            接続しました。最初の発言を準備しています…
          </div>
        )}

        {visible.map((t) => {
          const isStreaming = t.turn_id === streamingTurnId;

          // 調査メモ: 調査役（researcher / phase=research）のターンは persona 吹き出しでなく
          // 無彩色枠の「調査メモ」カードで描く。本文は Markdown＝出典 URL がリンク表示される。
          // 本文が空のまま検索中なら「調べています…」。
          if (t.speaker_id === "researcher" || t.phase === "research") {
            const time = formatTurnTime(t.ts);
            const searching = t.content === "" && isStreaming;
            return (
              <article
                key={t.turn_id}
                className="animate-turn-in rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-3.5 py-3"
              >
                <header className="flex flex-wrap items-center gap-x-2 gap-y-0.5 border-b border-[var(--color-line)] pb-1.5">
                  <Globe size={14} className="shrink-0 text-[var(--color-ink-muted)]" />
                  <span className="text-sm font-medium text-[var(--color-ink)]">
                    調査メモ
                  </span>
                  <span
                    className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]"
                  >
                    Web 検索
                  </span>
                  {t.query && (
                    <span className="min-w-0 max-w-full truncate text-[11px] text-[var(--color-ink-muted)]">
                      「{t.query}」
                    </span>
                  )}
                  {time && (
                    <>
                      <span className="text-[var(--color-line)]" aria-hidden="true">
                        ・
                      </span>
                      <span className="font-mono text-[11px] text-[var(--color-ink-muted)]">
                        {time}
                      </span>
                    </>
                  )}
                </header>
                {searching ? (
                  <p className="mt-2 flex items-start gap-2 text-sm leading-relaxed text-[var(--color-ink-muted)]">
                    <Search size={13} className="mt-0.5 shrink-0 animate-pulse-soft" />
                    <span className="min-w-0 [overflow-wrap:anywhere]">
                      {t.query
                        ? `「${t.query}」を調べています…（数十秒かかることがあります）`
                        : "Web で事実を調べています…（数十秒かかることがあります）"}
                    </span>
                  </p>
                ) : (
                  <div className="mt-2">
                    <Markdown>{t.content}</Markdown>
                    {/* 「流れて消える」不安への最小ラベル。詳しい説明と集約は右の「調べたこと」側に集約し、
                        ここは各ターンで反復しても煩くない短いチップに留める（報道トーンの簡潔さ）。 */}
                    <p className="mt-2 flex items-center gap-1.5 border-t border-[var(--color-line)] pt-1.5 text-[10px] text-[var(--color-ink-muted)]">
                      <Users size={11} className="shrink-0" />
                      全員に共有
                    </p>
                  </div>
                )}
              </article>
            );
          }

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
                    <Markdown>{t.content}</Markdown>
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
                {/* 本文が空のまま発言中なら「考え中」。本文があればストリーミング中でも Markdown で
                    描く（**強調** や箇条書きが生の記号で見えないように）。ストリーミング中は末尾に
                    点滅キャレットを添えてライブ感を保つ。delta 毎の再パースは討論規模なら十分軽い。 */}
                {t.content === "" && isStreaming ? (
                  <p className="mt-1 text-sm leading-relaxed">
                    <span className="text-[var(--color-ink-muted)]">考えています…</span>
                  </p>
                ) : (
                  <div className="mt-1">
                    <Markdown>{t.content}</Markdown>
                    {isStreaming && (
                      <span className="animate-pulse-soft -mt-1 inline-block align-middle text-[var(--color-ink-muted)]">
                        ▍
                      </span>
                    )}
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
      <div ref={endRef} />
    </div>
  );
}
