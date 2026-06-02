"use client";

import { useState } from "react";
import { KeyRound } from "lucide-react";

// BYOK のキー入力。キーは page 側で localStorage に保存し、ここは表示・編集だけを担う。
// 値の実体（value）は親が持ち、保存/クリアは onChange に委ねる（単方向データフロー）。
export function KeyEntry({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (key: string) => void;
  disabled?: boolean;
}) {
  const has = value.trim().length > 0;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  return (
    <div className="flex flex-col gap-1.5">
      <h2 className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
        <KeyRound size={12} /> APIキー（各自）
      </h2>

      {has && !editing ? (
        <div className="flex items-center justify-between gap-2 rounded-md border border-[var(--color-line)] px-2.5 py-1.5">
          <span className="text-xs text-[var(--color-ink)]">
            設定済み{" "}
            <span className="text-[var(--color-ink-muted)]">
              sk-…{value.trim().slice(-4)}
            </span>
          </span>
          <div className="flex shrink-0 gap-1.5">
            <button
              type="button"
              onClick={() => {
                setDraft("");
                setEditing(true);
              }}
              disabled={disabled}
              className="rounded px-1.5 py-0.5 text-[11px] text-[var(--color-ink-muted)] hover:text-[var(--color-accent)] disabled:opacity-40"
            >
              変更
            </button>
            <button
              type="button"
              onClick={() => onChange("")}
              disabled={disabled}
              className="rounded px-1.5 py-0.5 text-[11px] text-[var(--color-ink-muted)] hover:text-[var(--color-onair)] disabled:opacity-40"
            >
              クリア
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-1.5">
          <input
            type="password"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="sk-ant-..."
            disabled={disabled}
            autoComplete="off"
            spellCheck={false}
            className="rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-2.5 py-1.5 text-sm outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
          />
          <div className="flex gap-1.5">
            <button
              type="button"
              onClick={() => {
                onChange(draft);
                setEditing(false);
                setDraft("");
              }}
              disabled={disabled || !draft.trim()}
              className="rounded-md bg-[var(--color-accent)] px-2.5 py-1 text-[11px] font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              保存
            </button>
            {has && (
              <button
                type="button"
                onClick={() => {
                  setEditing(false);
                  setDraft("");
                }}
                className="rounded-md px-2.5 py-1 text-[11px] text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
              >
                取消
              </button>
            )}
          </div>
        </div>
      )}

      <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
        キーは<strong className="font-medium text-[var(--color-ink)]">このブラウザにのみ</strong>
        保存され、サーバには保存されません。実 LLM での討論にはご自身のキーが必要です（料金はご自身に課金）。{" "}
        <a
          href="https://console.anthropic.com/settings/keys"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-[var(--color-accent)]"
        >
          キーを取得
        </a>
      </p>
    </div>
  );
}
