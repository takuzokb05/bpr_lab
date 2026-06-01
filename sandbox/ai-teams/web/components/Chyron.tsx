"use client";

import { PHASE_LABELS } from "@/lib/types";

// 報道番組のテロップ（chyron）。running 中だけ、いま進行中のフェーズを画面上部に出す。
// 明朝でフェーズ名、左にアクセント深青の縦罫、帯は無彩色。グラデ・影・絵文字なし。
export function Chyron({
  phase,
  status,
}: {
  phase: string | null;
  status: "idle" | "running" | "paused" | "done" | "error";
}) {
  // running 以外、またはフェーズ未確定なら何も出さない（null 返しガード）。
  if (status !== "running" || !phase) return null;

  const label = PHASE_LABELS[phase] ?? phase;

  return (
    <div className="border-b border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-2">
      <div className="animate-chyron-in flex items-center gap-3">
        <span
          className="inline-block h-3.5 w-[2px]"
          style={{ backgroundColor: "var(--color-accent)" }}
          aria-hidden="true"
        />
        <span className="text-[10px] font-medium uppercase tracking-widest text-[var(--color-ink-muted)]">
          現在のフェーズ
        </span>
        <span className="font-display text-sm tracking-wide text-[var(--color-ink)]">
          {label}
        </span>
      </div>
    </div>
  );
}
