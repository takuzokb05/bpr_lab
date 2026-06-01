"use client";

import type { Turn } from "@/lib/types";
import { FileText } from "lucide-react";

export function MinutesPanel({
  synthesis,
  status,
}: {
  synthesis: Turn | null;
  status: "idle" | "running" | "done" | "error";
}) {
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
        {synthesis ? (
          <div className="animate-turn-in">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {synthesis.content}
            </p>
          </div>
        ) : (
          <p className="text-xs leading-relaxed text-[var(--color-ink-muted)]">
            {status === "running"
              ? "討論が進行中です。すべての発言が終わると、議長が議事録（合意点・対立点・リスク・ネクストアクション）をまとめます。"
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
