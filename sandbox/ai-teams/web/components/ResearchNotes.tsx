"use client";

import { useState } from "react";
import type { Turn } from "@/lib/types";
import { Globe, ExternalLink, ChevronDown } from "lucide-react";
import { Markdown } from "./Markdown";

// 調査ブリーフ本文から出典 URL を拾う（「出典:」節に限らず本文中の素 URL も拾う）。
const URL_RE = /https?:\/\/[^\s)>\]）」]+/g;

function extractUrls(text: string): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const m of (text ?? "").matchAll(URL_RE)) {
    // 末尾の句読点・閉じ括弧・Markdown 装飾記号(** _ ~ 等)を URL から外す。本文プローズ中に
    // モデルが **https://...** のように装飾付きで書いた素 URL を壊れた href にしないため。
    const u = m[0].replace(/[.,;:!?。、，；：！？)\]）」』】>*_~"'`]+$/u, "");
    if (!seen.has(u)) {
      seen.add(u);
      out.push(u);
    }
  }
  return out;
}

function hostOf(u: string): string {
  try {
    return new URL(u).hostname.replace(/^www\./, "");
  } catch {
    return u;
  }
}

/**
 * 「調べたこと」集約パネル。調査役（researcher）ターンを横断で集め、出典付きで一覧する。
 *
 * 狙い: 検索結果がタイムラインを流れて消えると「活きてるのか分からない」という声に応える。
 * ここで第一級の成果物として常設し、「以降の発言者全員に共有されている」ことを明示する。
 * 出典 URL を本文から抽出してリンク化（ホスト名表示）。本文は details で畳む。
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
  const [open, setOpen] = useState(false);
  const urls = extractUrls(turn.content);
  return (
    <li className="rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2">
      {turn.query && (
        <p className="mb-1 text-xs font-medium text-[var(--color-ink)] [overflow-wrap:anywhere]">
          「{turn.query}」
        </p>
      )}
      {urls.length > 0 && (
        <div className="flex flex-col gap-0.5">
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
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="mt-1.5 flex items-center gap-1 text-[11px] text-[var(--color-ink-muted)] hover:text-[var(--color-accent)]"
      >
        <ChevronDown
          size={12}
          className={`shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
        {open ? "調査結果を隠す" : "調査結果を表示"}
      </button>
      {open && (
        <div className="mt-1.5 [overflow-wrap:anywhere]">
          <Markdown>{turn.content}</Markdown>
        </div>
      )}
    </li>
  );
}
