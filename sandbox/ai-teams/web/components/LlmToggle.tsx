"use client";

// LLM の選択（既定は Mock = 無料）。実 LLM はキーが使えるときだけ選べる。
// キーの所在は BYOK モードで分岐する:
//   - byok=true: 各自のキー（keyAvailable = ブラウザにキーを保存済みか）
//   - byok=false（個人運用）: サーバの ANTHROPIC_API_KEY（keyAvailable = health.api_key_set）
// 二重課金を避けるため、初期値は false（mock）を page 側で持つ。
export function LlmToggle({
  useLlm,
  keyAvailable,
  byok,
  onChange,
  disabled,
}: {
  useLlm: boolean;
  keyAvailable: boolean;
  byok: boolean;
  onChange: (v: boolean) => void;
  disabled: boolean;
}) {
  const realLabel = keyAvailable
    ? "実LLM"
    : byok
      ? "実LLM（要キー）"
      : "実LLM（キー未設定）";
  const realTitle = keyAvailable
    ? undefined
    : byok
      ? "上の「APIキー（各自）」にご自身のキーを入力してください"
      : "ANTHROPIC_API_KEY が未設定です";

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
          disabled={disabled || !keyAvailable}
          title={realTitle}
          className={`flex-1 rounded px-2.5 py-1.5 text-xs transition-colors disabled:opacity-40 ${
            useLlm
              ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
              : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
          }`}
        >
          {realLabel}
        </button>
      </div>
    </div>
  );
}
