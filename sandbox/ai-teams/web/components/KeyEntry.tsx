"use client";

import { useState } from "react";
import { KeyRound, ShieldCheck } from "lucide-react";
import type { LlmProvider } from "@/lib/config";

// 各プロバイダの表示名・キー取得（＝上限設定）ページ。キーは各自が1社分だけ入れればよい。
const PROVIDER_META: Record<
  LlmProvider,
  { label: string; keyUrl: string; hint: string }
> = {
  anthropic: {
    label: "Anthropic",
    keyUrl: "https://console.anthropic.com/settings/keys",
    hint: "sk-ant-...",
  },
  openai: {
    label: "OpenAI",
    keyUrl: "https://platform.openai.com/api-keys",
    hint: "sk-...",
  },
  google: {
    label: "Google",
    keyUrl: "https://aistudio.google.com/apikey",
    hint: "AIza...",
  },
  // local（内製/開源）は鍵不要なので BYOK のキー選択には出さない（型を満たすためのみ定義）。
  local: {
    label: "内製/オープン",
    keyUrl: "#",
    hint: "キー不要",
  },
};

// BYOK のプロバイダ選択＋キー入力。キーは page 側で localStorage に保存し、ここは表示・編集だけ。
// プロバイダ切替時はキーをクリアする（別社のキーは流用できない＝単一キー運用）。
export function KeyEntry({
  provider,
  onProviderChange,
  value,
  onChange,
  providers,
  disabled,
}: {
  provider: LlmProvider;
  onProviderChange: (p: LlmProvider) => void;
  value: string;
  onChange: (key: string) => void;
  providers: LlmProvider[];
  disabled?: boolean;
}) {
  const has = value.trim().length > 0;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const meta = PROVIDER_META[provider];

  return (
    <div className="flex flex-col gap-2">
      <h2 className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
        <KeyRound size={12} /> APIキー（各自・1社分）
      </h2>

      {/* プロバイダ選択。切替でキーはクリア（別社のキーは使えない）。 */}
      <div className="flex rounded-md border border-[var(--color-line)] p-0.5">
        {providers.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => {
              if (p === provider) return;
              onProviderChange(p);
              onChange(""); // 別社へ切替＝キーを破棄
              setEditing(false);
              setDraft("");
            }}
            disabled={disabled}
            className={`flex-1 rounded px-1.5 py-1 text-[11px] transition-colors disabled:opacity-50 ${
              p === provider
                ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
                : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
            }`}
          >
            {PROVIDER_META[p].label}
          </button>
        ))}
      </div>

      {has && !editing ? (
        <div className="flex items-center justify-between gap-2 rounded-md border border-[var(--color-line)] px-2.5 py-1.5">
          <span className="text-xs text-[var(--color-ink)]">
            {meta.label} 設定済み{" "}
            <span className="text-[var(--color-ink-muted)]">…{value.trim().slice(-4)}</span>
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
            placeholder={`${meta.label} のキー（${meta.hint}）`}
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

      {/* 信頼の担保（正直な明記）。最強の実レバーは「上限付きの専用キー」。 */}
      <div className="flex flex-col gap-1 rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-2.5 py-2">
        <span className="flex items-center gap-1.5 text-[11px] font-medium text-[var(--color-ink)]">
          <ShieldCheck size={12} className="text-[var(--color-accent)]" /> キーの扱い
        </span>
        <ul className="flex flex-col gap-0.5 text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
          <li>・保存先は<strong className="font-medium text-[var(--color-ink)]">このブラウザのみ</strong>。サーバは保存・記録しません。</li>
          <li>・送信は HTTPS。あなたのセッションの LLM 呼び出しにのみ使います。</li>
          <li>
            ・<strong className="font-medium text-[var(--color-ink)]">上限付きの専用キー推奨</strong>（万一漏れても被害を限定）。{" "}
            <a
              href={meta.keyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-[var(--color-accent)]"
            >
              {meta.label} でキー作成/上限設定
            </a>
          </li>
          <li>・いつでも「クリア」、発行元でいつでも失効できます。料金はご自身に課金されます。</li>
        </ul>
      </div>
    </div>
  );
}
