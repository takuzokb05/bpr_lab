"use client";

/**
 * 討論モード（エンジン・プリセット）の選択。local 経路でサーバが提示する3択（クイック/
 * スタンダード/ディープ等）を出す。中身（モデル・応答の長さ）はサーバが解決するので、フロントは
 * id を送るだけ。「応答の長さ」セレクタの置き換え（local 時のみ。BYOK では従来の長さ選択を出す）。
 */
export function ModeSelect({
  presets,
  value,
  onChange,
  disabled,
}: {
  presets: { id: string; label: string; hint?: string }[];
  value: string;
  onChange: (id: string) => void;
  disabled?: boolean;
}) {
  if (!presets.length) return null;
  return (
    <div className="flex flex-col gap-1.5">
      <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
        討論モード
      </h2>
      <div className="flex rounded-md border border-[var(--color-line)] p-0.5">
        {presets.map((p) => {
          const active = p.id === value;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onChange(p.id)}
              disabled={disabled}
              title={p.hint}
              className={`flex flex-1 flex-col items-center gap-0.5 rounded px-1 py-1.5 text-xs transition-colors disabled:opacity-50 ${
                active
                  ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
                  : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
              }`}
            >
              <span className="font-medium">{p.label}</span>
              {p.hint && (
                <span className="text-[9px] leading-tight opacity-70">{p.hint}</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
