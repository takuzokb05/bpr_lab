"use client";

import type { Health } from "@/lib/sse";

// LLM の選択（既定は Mock = 無料）。実 LLM はキー設定済みのときだけ選べる。
// 二重課金を避けるため、初期値は false（mock）を page 側で持つ。
export function LlmToggle({
  useLlm,
  health,
  onChange,
  disabled,
}: {
  useLlm: boolean;
  health: Health | null;
  onChange: (v: boolean) => void;
  disabled: boolean;
}) {
  const keySet = health?.api_key_set ?? false;

  return (
    <div className="flex flex-col gap-1.5">
      <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
        応答エンジン
      </h2>
      <div className="flex rounded-md border border-[var(--color-line)] p-0.5">
        <button
          onClick={() => onChange(false)}
          disabled={disabled}
          className={`flex-1 rounded px-2.5 py-1.5 text-xs transition-colors disabled:opacity-50 ${
            !useLlm
              ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
              : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
          }`}
        >
          Mock（無料）
        </button>
        <button
          onClick={() => onChange(true)}
          disabled={disabled || !keySet}
          title={keySet ? undefined : "ANTHROPIC_API_KEY が未設定です"}
          className={`flex-1 rounded px-2.5 py-1.5 text-xs transition-colors disabled:opacity-40 ${
            useLlm
              ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
              : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
          }`}
        >
          {keySet ? "実LLM" : "実LLM（キー未設定）"}
        </button>
      </div>
    </div>
  );
}
