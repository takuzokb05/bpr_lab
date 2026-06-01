"use client";

import type { Turn } from "@/lib/types";
import { FileText, Sparkles } from "lucide-react";

// エグゼクティブサマリ（「結論:」「根拠:」「次の一手:」の3行）を行ごとに分解。
function parseSummary(text: string): { label: string; body: string }[] {
  const labels = ["結論", "根拠", "次の一手"];
  return text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .map((line) => {
      const hit = labels.find((lb) => line.startsWith(lb));
      if (hit) {
        return { label: hit, body: line.slice(hit.length).replace(/^[：:]\s*/, "") };
      }
      return { label: "", body: line };
    });
}

export function MinutesPanel({
  summary,
  synthesis,
  status,
}: {
  summary: Turn | null;
  synthesis: Turn | null;
  status: "idle" | "running" | "done" | "error";
}) {
  const summaryLines = summary ? parseSummary(summary.content) : [];

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-[var(--color-line)] px-5 py-4">
        <FileText size={15} className="text-[var(--color-ink-muted)]" />
        <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          成果（議事録）
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {/* エグゼクティブサマリ（最上段・意思決定者がまず読む） */}
        {summary && (
          <div className="animate-turn-in mb-5 rounded-md border border-[var(--color-accent)] bg-[var(--color-accent-weak)] p-4">
            <div className="mb-2 flex items-center gap-1.5">
              <Sparkles size={13} className="text-[var(--color-accent)]" />
              <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-accent)]">
                エグゼクティブサマリ
              </span>
            </div>
            <dl className="flex flex-col gap-1.5">
              {summaryLines.map((l, i) =>
                l.label ? (
                  <div key={i} className="flex gap-2 text-sm leading-relaxed">
                    <dt className="shrink-0 font-medium text-[var(--color-accent)]">
                      {l.label}
                    </dt>
                    <dd>{l.body}</dd>
                  </div>
                ) : (
                  <p key={i} className="text-sm leading-relaxed">
                    {l.body}
                  </p>
                )
              )}
            </dl>
          </div>
        )}

        {/* 議事録本体（合意/対立/リスク/アクション） */}
        {synthesis ? (
          <div className="animate-turn-in">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {synthesis.content}
            </p>
          </div>
        ) : (
          !summary && (
            <p className="text-xs leading-relaxed text-[var(--color-ink-muted)]">
              {status === "running"
                ? "討論が進行中です。すべての発言が終わると、議長が要約と議事録（合意点・対立点・リスク・ネクストアクション）をまとめます。"
                : "討論が終わると、ここに要約と議事のまとめが表示されます。"}
            </p>
          )
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
