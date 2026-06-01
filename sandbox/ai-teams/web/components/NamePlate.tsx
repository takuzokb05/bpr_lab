"use client";

import { PHASE_LABELS, formatTurnTime } from "@/lib/types";

// 発言ヘッダの名札。「名前 ・ フェーズ ・ 時刻」を中黒で区切り、下に 1px の罫線のみ。
// 影は付けない（報道トーンの静かな階層づけ）。時刻は formatTurnTime で HH:mm（無ければ空）。
export function NamePlate({
  name,
  phase,
  ts,
}: {
  name: string;
  phase: string;
  ts?: number;
}) {
  const phaseLabel = PHASE_LABELS[phase] ?? phase;
  const time = formatTurnTime(ts);

  return (
    <header className="flex items-baseline gap-2 border-b border-[var(--color-line)] pb-1">
      <span className="text-sm font-medium text-[var(--color-ink)]">{name}</span>
      <span className="text-[var(--color-line)]" aria-hidden="true">
        ・
      </span>
      <span className="text-[11px] text-[var(--color-ink-muted)]">{phaseLabel}</span>
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
  );
}
