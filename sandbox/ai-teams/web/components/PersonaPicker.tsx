"use client";

import { useMemo, useState } from "react";
import { CATEGORY_LABELS, type Persona, type PersonaCategory } from "@/lib/types";
import { Avatar } from "./Avatar";
import { Check, Search, ChevronDown, ChevronRight, Settings2 } from "lucide-react";

const CATEGORY_ORDER: PersonaCategory[] = [
  "facilitation",
  "thinking",
  "founders",
  "philosophers",
  "chair",
  "scribe",
];

export function PersonaPicker({
  personas,
  selected,
  onToggle,
  disabled,
  onManage,
}: {
  personas: Persona[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  disabled: boolean;
  // 指定時のみ「管理」ボタンを出す。
  onManage?: () => void;
}) {
  const [query, setQuery] = useState("");
  const [activeTags, setActiveTags] = useState<Set<string>>(new Set());
  const [collapsed, setCollapsed] = useState<Set<PersonaCategory>>(new Set());

  // 全タグ（出現順・重複なし）。
  const allTags = useMemo(() => {
    const seen: string[] = [];
    for (const p of personas) for (const t of p.tags) if (!seen.includes(t)) seen.push(t);
    return seen;
  }, [personas]);

  // 検索（名前/ID）＋タグ OR 絞り込み。
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return personas.filter((p) => {
      const hitQ =
        !q ||
        p.display_name.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q);
      const hitTag =
        activeTags.size === 0 || p.tags.some((t) => activeTags.has(t));
      return hitQ && hitTag;
    });
  }, [personas, query, activeTags]);

  const groups = CATEGORY_ORDER.map((cat) => ({
    cat,
    items: filtered.filter((p) => p.category === cat),
  })).filter((g) => g.items.length > 0);

  function toggleTag(tag: string) {
    setActiveTags((prev) => {
      const next = new Set(prev);
      next.has(tag) ? next.delete(tag) : next.add(tag);
      return next;
    });
  }

  function toggleCollapse(cat: PersonaCategory) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
            編成
          </h2>
          <p className="mt-1 text-xs text-[var(--color-ink-muted)]">
            {selected.size} 名を選択中
          </p>
        </div>
        {onManage && (
          <button
            onClick={onManage}
            disabled={disabled}
            className="flex items-center gap-1 text-[11px] text-[var(--color-ink-muted)] hover:text-[var(--color-accent)] disabled:opacity-50"
          >
            <Settings2 size={13} /> 管理
          </button>
        )}
      </div>

      {/* 検索 */}
      <div className="relative">
        <Search
          size={13}
          className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-ink-muted)]"
        />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="名前・IDで検索"
          className="w-full rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] py-1.5 pl-8 pr-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
        />
      </div>

      {/* タグ chip（OR 絞り込み） */}
      {allTags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {allTags.map((t) => {
            const on = activeTags.has(t);
            return (
              <button
                key={t}
                onClick={() => toggleTag(t)}
                className={`rounded-full border px-2 py-0.5 text-[11px] transition-colors ${
                  on
                    ? "border-[var(--color-accent)] bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
                    : "border-[var(--color-line)] text-[var(--color-ink-muted)] hover:border-[var(--color-ink-muted)]"
                }`}
              >
                {t}
              </button>
            );
          })}
        </div>
      )}

      {groups.length === 0 && (
        <p className="text-xs text-[var(--color-ink-muted)]">
          該当するペルソナがありません。
        </p>
      )}

      {groups.map((g) => {
        const isCollapsed = collapsed.has(g.cat);
        return (
          <div key={g.cat} className="flex flex-col gap-1.5">
            <button
              onClick={() => toggleCollapse(g.cat)}
              className="flex items-center gap-1 text-left text-[11px] font-medium text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
            >
              {isCollapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
              {CATEGORY_LABELS[g.cat]}
            </button>
            {!isCollapsed &&
              g.items.map((p) => {
                const on = selected.has(p.id);
                return (
                  <button
                    key={p.id}
                    onClick={() => onToggle(p.id)}
                    disabled={disabled}
                    className={`group flex items-center gap-3 rounded-md border px-2.5 py-2 text-left transition-colors disabled:opacity-50 ${
                      on
                        ? "border-[var(--color-accent)] bg-[var(--color-accent-weak)]"
                        : "border-[var(--color-line)] bg-[var(--color-surface)] hover:border-[var(--color-ink-muted)]"
                    }`}
                  >
                    <Avatar monogram={p.monogram} accent={p.accent} size={30} />
                    <span className="flex min-w-0 flex-1 flex-col">
                      <span className="truncate text-sm">{p.display_name}</span>
                      {p.model && (
                        <span className="truncate font-mono text-[10px] text-[var(--color-ink-muted)]">
                          {p.model}
                        </span>
                      )}
                    </span>
                    {on && <Check size={15} className="text-[var(--color-accent)]" />}
                  </button>
                );
              })}
          </div>
        );
      })}
    </div>
  );
}
