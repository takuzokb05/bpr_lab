"use client";

import { PHASE_LABELS } from "@/lib/types";

// 報道番組のテロップ（chyron）。running 中だけ、いま進行中のフェーズを画面上部に出す。
// 明朝でフェーズ名、左にアクセント深青の縦罫、帯は無彩色。グラデ・影・絵文字なし。
// 右端に「発散 → 批判 → 収束 → 裁定」の進行アークを常設し、この討論が最後に
// 裁定（答え）へ向かっていることを観ている間ずっと予告する（到達点の期待を作る）。

// 進行アークの4駅。phase（API値）→ 駅 index。followup/human/research 等の脇道は -1（強調なし）。
const ARC_STEPS = ["発散", "批判", "収束", "裁定"] as const;
const PHASE_TO_STEP: Record<string, number> = {
  発散: 0,
  bridge: 0,
  批判: 1,
  収束: 2,
  closing: 2,
  synthesis: 3,
  verdict: 3,
};

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
  const step = PHASE_TO_STEP[phase] ?? -1;

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

        {/* 進行アーク: 現在地はアクセント、通過済みはインク、未到達は淡色。 */}
        <span
          className="ml-auto hidden items-center gap-1.5 sm:flex"
          aria-label={`進行: 発散、批判、収束、裁定${step >= 0 ? `。現在は${ARC_STEPS[step]}` : ""}`}
        >
          {ARC_STEPS.map((s, i) => (
            <span key={s} className="flex items-center gap-1.5">
              {i > 0 && (
                <span className="text-[9px] text-[var(--color-ink-muted)]" aria-hidden="true">
                  →
                </span>
              )}
              <span
                className={`text-[10px] tracking-wider ${
                  step === i
                    ? "font-medium text-[var(--color-accent)]"
                    : step > i
                      ? "text-[var(--color-ink)]"
                      : "text-[var(--color-ink-muted)] opacity-60"
                }`}
              >
                {s}
              </span>
            </span>
          ))}
        </span>
      </div>
    </div>
  );
}
