"use client";

import { useState } from "react";
import type { Turn } from "@/lib/types";
import {
  buildMeetingMarkdown,
  meetingFilename,
  copyText,
  downloadMarkdown,
  sectionAvailability,
  type ExportOptions,
} from "@/lib/export";
import { Copy, Check, Download } from "lucide-react";

// 書き出すセクションの並び（ドキュメント順と一致：要約→調査結果→会議内容）。
const SECTIONS: { key: keyof ExportOptions; label: string }[] = [
  { key: "summary", label: "議事録" },
  { key: "research", label: "調査結果" },
  { key: "body", label: "会議内容" },
];

/**
 * 会議結果の書き出しバー。要約/調査結果/会議内容をチェックで選び（既定すべて ON）、
 * コピー or Markdown 保存する。中身の無いセクションのチェックは無効化する。
 * 手持ちの LLM にそのまま投げられる素の Markdown を 1ファイルにまとめる。
 */
export function ExportBar({ topic, turns }: { topic: string | null; turns: Turn[] }) {
  const [opts, setOpts] = useState<ExportOptions>({
    summary: true,
    research: true,
    body: true,
  });
  const [copied, setCopied] = useState(false);

  const avail = sectionAvailability(turns);
  // 実際に出力するのは「選択 AND 中身あり」。表示チェックも同じ条件にする。
  const effective: ExportOptions = {
    summary: opts.summary && avail.summary,
    research: opts.research && avail.research,
    body: opts.body && avail.body,
  };
  const md = buildMeetingMarkdown(topic ?? "", turns, effective);
  const nothingSelected = !effective.summary && !effective.research && !effective.body;

  async function onCopy() {
    if (nothingSelected) return;
    const ok = await copyText(md);
    if (ok) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }

  function onDownload() {
    if (nothingSelected) return;
    downloadMarkdown(meetingFilename(topic ?? ""), md);
  }

  return (
    <div className="shrink-0 border-t border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-3">
      <div className="flex items-center gap-2">
        <Download size={13} className="text-[var(--color-ink-muted)]" />
        <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          書き出し
        </span>
      </div>

      {/* セクション選択（中身が無ければ無効） */}
      <div className="mt-2 flex flex-wrap gap-1.5">
        {SECTIONS.map(({ key, label }) => {
          const enabled = avail[key];
          const checked = effective[key];
          return (
            <button
              key={key}
              type="button"
              role="checkbox"
              aria-checked={checked}
              disabled={!enabled}
              onClick={() => setOpts((o) => ({ ...o, [key]: !o[key] }))}
              className={`flex items-center gap-1 rounded-md border px-2 py-1 text-[11px] transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                checked
                  ? "border-[var(--color-accent)] bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
                  : "border-[var(--color-line)] text-[var(--color-ink-muted)] hover:border-[var(--color-ink-muted)]"
              }`}
            >
              <span
                aria-hidden="true"
                className={`flex h-3 w-3 items-center justify-center rounded-[3px] border ${
                  checked
                    ? "border-[var(--color-accent)] bg-[var(--color-accent)] text-white"
                    : "border-[var(--color-line)]"
                }`}
              >
                {checked && <Check size={9} strokeWidth={3} />}
              </span>
              {label}
            </button>
          );
        })}
      </div>

      {/* アクション */}
      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          onClick={onCopy}
          disabled={nothingSelected}
          className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-2.5 py-1.5 text-xs hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] disabled:opacity-40 disabled:hover:border-[var(--color-line)] disabled:hover:text-[var(--color-ink)]"
        >
          {copied ? <Check size={13} className="text-[var(--color-accent)]" /> : <Copy size={13} />}
          {copied ? "コピーしました" : "コピー"}
        </button>
        <button
          type="button"
          onClick={onDownload}
          disabled={nothingSelected}
          className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-2.5 py-1.5 text-xs hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] disabled:opacity-40 disabled:hover:border-[var(--color-line)] disabled:hover:text-[var(--color-ink)]"
        >
          <Download size={13} /> Markdown 保存
        </button>
      </div>
    </div>
  );
}
