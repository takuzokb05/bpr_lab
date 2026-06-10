"use client";

// 開演前の議場（idle 時の中央ステージ）。従来は説明文1行の空白で、初見は何を投げればよいか
// 分からず、再訪者には前回の続きへの導線が無かった。ここを「席に着いた登壇者＋裁定への道筋＋
// 議題例＋前回の続き」で、討論が始まる前から番組としての期待を作る。装飾は既存の規律に従う
// （グラデ・影・絵文字なし。罫線・余白・明朝で階層を作る）。

import type { HistoryEntry } from "@/lib/config";
import { Avatar } from "./Avatar";
import { Gavel, Play } from "lucide-react";

export interface SeatedPersona {
  id: string;
  name: string;
  monogram: string;
  accent: string;
  role?: string; // 進行役の役名（"司会"/"議長"）。パネリストは undefined
}

// 前回討論の「答え」抜粋: 裁定 → 議事録 → なし の順で拾い、Markdown 記号を軽く落とす。
function lastAnswerExcerpt(entry: HistoryEntry): string | null {
  for (const phase of ["verdict", "synthesis"]) {
    const all = entry.turns.filter(
      (t) => t.phase === phase && (t.content ?? "").trim().length > 0
    );
    if (all.length) {
      const raw = all[all.length - 1].content;
      const plain = raw
        .replace(/^#+\s*/gm, "")
        .replace(/[*_`>]/g, "")
        .replace(/\s+/g, " ")
        .trim();
      return plain.length > 110 ? plain.slice(0, 110) + "…" : plain;
    }
  }
  return null;
}

export function IdleStage({
  seated,
  examples,
  onPickExample,
  lastEntry,
  onOpenLast,
}: {
  seated: SeatedPersona[];
  examples: string[];
  onPickExample: (topic: string) => void;
  lastEntry: HistoryEntry | null;
  onOpenLast: (entry: HistoryEntry) => void;
}) {
  const excerpt = lastEntry ? lastAnswerExcerpt(lastEntry) : null;
  const panelists = seated.filter((s) => !s.role);

  return (
    <div className="flex h-full flex-col overflow-y-auto px-6 py-8">
      <div className="mx-auto w-full max-w-xl">
        {/* 開演前の見出し */}
        <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          本日の登壇者
        </p>

        {/* 席に着いた登壇者。編成（左パネル）の選択がそのまま反映される＝「呼んだ顔ぶれ」が見える。 */}
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-3 border-b border-[var(--color-line)] pb-5">
          {seated.map((s) => (
            <div key={s.id} className="flex w-14 flex-col items-center gap-1.5">
              <Avatar monogram={s.monogram} accent={s.accent} size={40} />
              <span className="w-full truncate text-center text-[10px] leading-tight text-[var(--color-ink)]">
                {s.name}
              </span>
              {s.role && (
                <span className="-mt-1 text-[9px] text-[var(--color-ink-muted)]">{s.role}</span>
              )}
            </div>
          ))}
          {panelists.length === 0 && (
            <p className="self-center text-xs leading-relaxed text-[var(--color-ink-muted)]">
              パネリストがまだいません。左の「編成」から呼んでください。
            </p>
          )}
        </div>

        {/* 番組の道筋＝答え（裁定）への期待を最初に作る。 */}
        <p className="mt-5 text-sm leading-relaxed text-[var(--color-ink)]">
          議題を一つ投げてください。登壇者が
          <span className="mx-1 text-[var(--color-ink-muted)]">発散 → 批判 → 収束</span>
          と討論し、最後に議長が
          <span className="font-display mx-1 text-[var(--color-accent)]">裁定</span>
          ——あなたの議題への答え——を下します。
        </p>

        {/* 議題例: 初見の「何を投げればいいか分からない」をワンタップで越えさせる。 */}
        <div className="mt-5">
          <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
            例えばこんな議題
          </p>
          <div className="mt-2 flex flex-col items-start gap-1.5">
            {examples.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => onPickExample(ex)}
                className="max-w-full rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-3 py-1.5 text-left text-xs leading-relaxed text-[var(--color-ink)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        {/* おかえりカード: 前回の討論がどこに着地したかを見せ、思考の続きへ誘う（再訪の理由）。 */}
        {lastEntry && (
          <div className="mt-7 rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-3.5">
            <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
              前回の討論
            </p>
            <p className="mt-1.5 truncate text-sm font-medium text-[var(--color-ink)]">
              {lastEntry.topic}
            </p>
            {excerpt && (
              <p className="mt-1.5 flex items-start gap-1.5 text-xs leading-relaxed text-[var(--color-ink-muted)]">
                <Gavel size={12} className="mt-0.5 shrink-0 text-[var(--color-accent)]" />
                <span>{excerpt}</span>
              </p>
            )}
            <button
              type="button"
              onClick={() => onOpenLast(lastEntry)}
              className="mt-2.5 flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs text-[var(--color-ink)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
            >
              <Play size={12} /> 開いて続きから深める
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
