"use client";

import { useState } from "react";
import type { Turn } from "@/lib/types";
import { Globe, ExternalLink, ChevronDown, Search } from "lucide-react";
import { Markdown } from "./Markdown";
import { splitBrief, hostOf } from "@/lib/research";

/**
 * 「調べたこと」集約パネル。調査役（researcher）ターンを横断で集め、出典付きで一覧する。
 *
 * 狙い: 検索結果がタイムラインを流れて消えると「活きてるのか分からない」という声に応える。
 * ここで第一級の成果物として常設し、「以降の発言者全員に共有されている」ことを明示する。
 * 各項目は「検索クエリ → 調査結果（常時表示）→ 出典（折り畳み）」の順。出典は数が多くなりがちなので
 * 既定で畳み、本文（findings）と二重表示しないよう "出典:" 節で分離する。
 */
export function ResearchNotes({ research }: { research: Turn[] }) {
  // 本文が出そろったものだけ（検索中の空ターンは除く）。
  const items = research.filter((t) => (t.content ?? "").trim().length > 0);
  if (items.length === 0) return null;

  return (
    <section className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-[var(--color-line)] px-5 py-3">
        <Globe size={14} className="text-[var(--color-ink-muted)]" />
        <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          調べたこと（{items.length}件）
        </h2>
      </div>
      <p className="px-5 pt-2.5 text-[10px] leading-relaxed text-[var(--color-ink-muted)]">
        Web 検索で集めた事実です。
        <strong className="font-medium text-[var(--color-ink)]">以降の発言者全員に共有</strong>
        され、議論の土台になっています。
      </p>
      <ul className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-5 py-2.5">
        {items.map((t) => (
          <ResearchItem key={t.turn_id} turn={t} />
        ))}
      </ul>
    </section>
  );
}

function ResearchItem({ turn }: { turn: Turn }) {
  // 並び順: 検索クエリ → 調査結果（最初から表示）→ 出典（折り畳み・既定で閉じる）。
  const [showSources, setShowSources] = useState(false);
  const { findings, urls, hadSourcesSection } = splitBrief(turn.content);
  return (
    <li className="rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2">
      {/* 1. 検索クエリ */}
      {turn.query && (
        <p className="mb-1 flex items-start gap-1 text-xs font-medium text-[var(--color-ink)] [overflow-wrap:anywhere]">
          <Search size={11} className="mt-0.5 shrink-0 text-[var(--color-ink-muted)]" />
          <span>「{turn.query}」</span>
        </p>
      )}
      {/* 2. 調査結果（最初から見える） */}
      <div className="[overflow-wrap:anywhere]">
        <Markdown>{findings}</Markdown>
      </div>
      {/* 3. 出典（多くなりがちなので折り畳み・既定で閉じる）。出典節を分離できたときだけ＝
          本文にインライン URL が残っていないときだけ別枠を出す（二重表示の回避）。 */}
      {hadSourcesSection && urls.length > 0 && (
        <div className="mt-1.5 border-t border-[var(--color-line)] pt-1.5">
          <button
            type="button"
            onClick={() => setShowSources((v) => !v)}
            className="flex items-center gap-1 text-[11px] text-[var(--color-ink-muted)] hover:text-[var(--color-accent)]"
          >
            <ChevronDown
              size={12}
              className={`shrink-0 transition-transform ${showSources ? "rotate-180" : ""}`}
            />
            出典 {urls.length} 件{showSources ? "を隠す" : "を表示"}
          </button>
          {showSources && (
            <div className="mt-1 flex flex-col gap-0.5">
              {urls.map((u) => (
                <a
                  key={u}
                  href={u}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[11px] text-[var(--color-accent)] hover:underline"
                >
                  <ExternalLink size={11} className="shrink-0" />
                  <span className="truncate">{hostOf(u)}</span>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </li>
  );
}
