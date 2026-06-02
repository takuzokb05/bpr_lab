"use client";

import type { Verbosity } from "@/lib/config";

// 応答の長さ。ユーザーはトークン数を意識せず「質感」だけ選ぶ。裏で max_tokens 上限＋
// 発話スタイル指示にマップされる（既定 standard）。
const OPTIONS: { id: Verbosity; label: string; note: string }[] = [
  { id: "brief", label: "簡潔", note: "要点だけ短く。コスト最小・速い。" },
  { id: "standard", label: "標準", note: "ふつうの長さ。多くの議題はこれで足りる。" },
  {
    id: "deep",
    label: "じっくり",
    note: "具体例・根拠・想定反論まで踏み込む。重い議題向け（コスト増）。",
  },
];

export function VerbositySelect({
  value,
  onChange,
  disabled,
}: {
  value: Verbosity;
  onChange: (v: Verbosity) => void;
  disabled?: boolean;
}) {
  const note = OPTIONS.find((o) => o.id === value)?.note ?? "";
  return (
    <div className="flex flex-col gap-1.5">
      <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
        応答の長さ
      </h2>
      <div className="flex rounded-md border border-[var(--color-line)] p-0.5">
        {OPTIONS.map((o) => (
          <button
            key={o.id}
            type="button"
            onClick={() => onChange(o.id)}
            disabled={disabled}
            className={`flex-1 rounded px-2 py-1.5 text-xs transition-colors disabled:opacity-50 ${
              value === o.id
                ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
                : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
      <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">{note}</p>
    </div>
  );
}
