"use client";

import type { Turn } from "@/lib/types";
import { FileText, Gavel } from "lucide-react";
import { Markdown } from "./Markdown";

export function MinutesPanel({
  synthesis,
  verdict,
  status,
  streaming = false,
  verdictStreaming = false,
}: {
  synthesis: Turn | null;
  verdict: Turn | null; // 裁定（議長の結論）。議事録の後に出る＝成果の筆頭
  status: "idle" | "running" | "paused" | "done" | "error";
  streaming?: boolean; // 議事録が今ストリーミング生成中か（生成中表示・末尾キャレット用）
  verdictStreaming?: boolean; // 裁定が今ストリーミング生成中か
}) {
  const hasMinutes = !!synthesis && synthesis.content.trim().length > 0;
  const hasVerdict = !!verdict && verdict.content.trim().length > 0;
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-[var(--color-line)] px-5 py-4">
        <FileText size={15} className="text-[var(--color-ink-muted)]" />
        <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          成果（裁定と議事録）
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {/* 裁定（結論）を筆頭に置く。依頼者への答え＝このツールの成果物の主役。 */}
        {(hasVerdict || (verdict && verdictStreaming)) && (
          <section className="animate-turn-in mb-4 rounded-md border border-[var(--color-accent)] px-3.5 py-3">
            <h3 className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-[var(--color-accent)]">
              <Gavel size={12} /> 裁定（結論）
            </h3>
            {hasVerdict ? (
              <div className="mt-2">
                <Markdown>{verdict!.content}</Markdown>
                {verdictStreaming && (
                  <span className="animate-pulse-soft -mt-1 inline-block align-middle text-[var(--color-ink-muted)]">
                    ▍
                  </span>
                )}
              </div>
            ) : (
              <p className="mt-2 flex items-start gap-2 text-sm leading-relaxed text-[var(--color-ink)]">
                <span className="animate-pulse-soft mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full bg-[var(--color-accent)]" />
                裁定を下しています…
              </p>
            )}
          </section>
        )}

        {/* 議事録本体（残った対立点/少数意見/リスク/合意/アクション）。議長の統合を1枚で表示。 */}
        {hasMinutes ? (
          <div className="animate-turn-in">
            {hasVerdict && (
              <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
                議事録
              </h3>
            )}
            <Markdown>{synthesis!.content}</Markdown>
            {streaming && (
              <span className="animate-pulse-soft -mt-1 inline-block align-middle text-[var(--color-ink-muted)]">
                ▍
              </span>
            )}
          </div>
        ) : synthesis ? (
          // synthesis ターンは来たが本文未着＝生成中（議事録は時間がかかるので明示する）。
          <p className="flex items-start gap-2 text-sm leading-relaxed text-[var(--color-ink)]">
            <span className="animate-pulse-soft mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full bg-[var(--color-accent)]" />
            議事録を生成しています…（数十秒かかることがあります）
          </p>
        ) : (
          <p className="text-xs leading-relaxed text-[var(--color-ink-muted)]">
            {status === "running"
              ? "討論が進行中です。すべての発言が終わると、議長が議事録（対立点・リスク・合意点）と裁定（あなたの議題への結論）をまとめます。"
              : status === "paused"
                ? "本編が終わり、議場を開いています。下のパネルで追い質問を続けるか、「結論を出す」で議長に裁定と議事録をまとめさせてください。"
                : status === "done" || status === "error"
                  ? "この討論は裁定・議事録を作成せずに終了しました（本編の記録はタイムラインに残っています）。"
                  : "討論が終わると、ここに裁定（結論）と議事のまとめが表示されます。"}
          </p>
        )}
      </div>

      {/* AI討論である旨の免責（B4・誤誘導防止） */}
      <div className="border-t border-[var(--color-line)] px-5 py-2.5">
        <p className="text-[10px] leading-relaxed text-[var(--color-ink-muted)]">
          これはAIによる討論シミュレーションです。事実の正確性は保証されません。
          著名人ペルソナは公開情報に基づく演出（「演」）であり、本人の見解ではありません。
        </p>
      </div>
    </div>
  );
}
