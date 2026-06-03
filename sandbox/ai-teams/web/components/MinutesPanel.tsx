"use client";

import type { Turn } from "@/lib/types";
import { FileText } from "lucide-react";
import { Markdown } from "./Markdown";

export function MinutesPanel({
  synthesis,
  status,
  streaming = false,
}: {
  synthesis: Turn | null;
  status: "idle" | "running" | "paused" | "done" | "error";
  streaming?: boolean; // 議事録が今ストリーミング生成中か（生成中表示・末尾キャレット用）
}) {
  const hasMinutes = !!synthesis && synthesis.content.trim().length > 0;
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-[var(--color-line)] px-5 py-4">
        <FileText size={15} className="text-[var(--color-ink-muted)]" />
        <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          成果（議事録）
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {/* 議事録本体（合意/対立/リスク/アクション）。議長の統合を1枚で表示。 */}
        {hasMinutes ? (
          <div className="animate-turn-in">
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
              ? "討論が進行中です。すべての発言が終わると、議長が議事録（合意点・対立点・リスク・ネクストアクション）をまとめます。"
              : status === "paused"
                ? "本編が終わり、議場を開いています。下のパネルで追い質問を続けるか、「議事録を作る」で議長にまとめさせてください。"
                : status === "done" || status === "error"
                  ? "この討論は議事録を作成せずに終了しました（本編の記録はタイムラインに残っています）。"
                  : "討論が終わると、ここに議事のまとめが表示されます。"}
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
