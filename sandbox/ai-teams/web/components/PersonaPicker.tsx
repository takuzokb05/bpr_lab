"use client";

import { useMemo, useState } from "react";
import { CATEGORY_LABELS, type Persona, type PersonaCategory } from "@/lib/types";
import { Avatar } from "./Avatar";
import { Check, Search, ChevronDown, ChevronRight, Settings2, Plus } from "lucide-react";

// ピッカーに出すのは「議論する人＝パネリスト」だけ。司会(facilitation)・議長(chair)は
// 進行の固定役として自動で含めるためトグル表示しない。書記(scribe)は発言しない死に役なので除外。
const CATEGORY_ORDER: PersonaCategory[] = ["thinking", "founders", "philosophers"];

export function PersonaPicker({
  personas,
  selected,
  onToggle,
  disabled,
  onManage,
  onAddOwn,
  autoRoles = [],
}: {
  personas: Persona[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  disabled: boolean;
  // 指定時のみ「管理」ボタンを出す（readonly では page 側が渡さない＝非表示）。
  onManage?: () => void;
  // 「自分のペルソナ」（クライアント定義）ドロワーを開く。readonly でも使える。
  onAddOwn?: () => void;
  // 自動で含める進行役（司会・議長）。固定行で明示するだけでトグルはしない。
  autoRoles?: Persona[];
}) {
  const [query, setQuery] = useState("");
  const [activeTags, setActiveTags] = useState<Set<string>>(new Set());
  const [collapsed, setCollapsed] = useState<Set<PersonaCategory>>(new Set());
  // 「詳細」を展開しているペルソナ id 群（複数同時に開ける）。
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

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
        p.id.toLowerCase().includes(q) ||
        (p.description ?? "").toLowerCase().includes(q) ||
        (p.detail ?? "").toLowerCase().includes(q);
      const hitTag =
        activeTags.size === 0 || p.tags.some((t) => activeTags.has(t));
      return hitQ && hitTag;
    });
  }, [personas, query, activeTags]);

  const groups = CATEGORY_ORDER.map((cat) => ({
    cat,
    items: filtered.filter((p) => p.category === cat),
  })).filter((g) => g.items.length > 0);

  // 因縁サジェスト: 選択済みペルソナの対立/盟友相手のうち、まだ選んでいない人を提示。
  // クリックで編成に足せる＝「火花の散る組み合わせ」を狙って作れる。
  const REL_LABEL: Record<string, string> = {
    rival: "対立",
    ally: "盟友",
    mentor: "師弟",
    student: "師弟",
  };
  const rivalrySuggestions = useMemo(() => {
    const byId = new Map(personas.map((p) => [p.id, p]));
    const out: { persona: Persona; type: string }[] = [];
    const seen = new Set<string>();
    for (const p of personas) {
      if (!selected.has(p.id)) continue;
      for (const rel of p.relationships ?? []) {
        if (selected.has(rel.to) || seen.has(rel.to)) continue;
        const target = byId.get(rel.to);
        if (!target) continue;
        seen.add(rel.to);
        out.push({ persona: target, type: rel.type });
      }
    }
    return out;
  }, [personas, selected]);

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

  function toggleExpand(id: string) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
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
            パネリスト {selected.size} 名
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {onAddOwn && (
            <button
              onClick={onAddOwn}
              disabled={disabled}
              className="flex items-center gap-1 text-[11px] text-[var(--color-ink-muted)] hover:text-[var(--color-accent)] disabled:opacity-50"
            >
              <Plus size={13} /> 自分の
            </button>
          )}
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
      </div>

      {/* 進行役（固定・自動で含む）。司会＝オープニング、議長＝議事録。トグル不可。 */}
      {autoRoles.length > 0 && (
        <div className="flex flex-col gap-1 rounded-md border border-dashed border-[var(--color-line)] px-2.5 py-2">
          <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
            進行役（自動）
          </span>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {autoRoles.map((p) => (
              <span key={p.id} className="flex items-center gap-1.5 text-xs text-[var(--color-ink)]">
                <Avatar monogram={p.monogram} accent={p.accent} size={18} />
                {p.display_name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 検索 */}
      <div className="relative">
        <Search
          size={13}
          className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-ink-muted)]"
        />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="名前・説明で検索"
          aria-label="ペルソナを名前・説明で検索"
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

      {/* 因縁で足す（選択中ペルソナの対立/盟友相手を提案。クリックで編成に追加） */}
      {rivalrySuggestions.length > 0 && (
        <div className="flex flex-col gap-1.5 rounded-md border border-dashed border-[var(--color-line)] px-2.5 py-2">
          <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
            因縁で足す
          </span>
          <div className="flex flex-wrap gap-1.5">
            {rivalrySuggestions.map(({ persona, type }) => (
              <button
                key={persona.id}
                onClick={() => onToggle(persona.id)}
                disabled={disabled}
                title={`${persona.display_name} を編成に足す`}
                className="flex items-center gap-1 rounded-full border border-[var(--color-line)] px-2 py-0.5 text-[11px] text-[var(--color-ink-muted)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] disabled:opacity-50"
              >
                <span
                  className={
                    type === "ally" ? "text-[var(--color-accent)]" : "text-[var(--color-onair)]"
                  }
                >
                  {REL_LABEL[type] ?? "因縁"}
                </span>
                {persona.display_name}
                <Plus size={11} />
              </button>
            ))}
          </div>
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
                const expanded = expandedIds.has(p.id);
                // 「詳細」で出す中身。detail（充実説明）優先、無ければ description にフォールバック。
                const detailText = p.detail || p.description || "";
                const panelId = `persona-detail-${p.id}`;
                return (
                  <div
                    key={p.id}
                    className={`overflow-hidden rounded-md border transition-colors ${
                      disabled ? "opacity-60" : ""
                    } ${
                      on
                        ? "border-[var(--color-accent)] bg-[var(--color-accent-weak)]"
                        : "border-[var(--color-line)] bg-[var(--color-surface)] hover:border-[var(--color-ink-muted)]"
                    }`}
                  >
                    <div className="flex items-stretch">
                      {/* 選択トグル（行本体）。詳細ボタンと別 button にしてネストを避ける。
                          dim は行全体（外側 div）に掛けるのでここでは opacity を持たせない。 */}
                      <button
                        onClick={() => onToggle(p.id)}
                        disabled={disabled}
                        aria-pressed={on}
                        className="flex min-w-0 flex-1 items-center gap-3 px-2.5 py-2 text-left focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[var(--color-accent)]"
                      >
                        <Avatar monogram={p.monogram} accent={p.accent} size={30} />
                        <span className="flex min-w-0 flex-1 flex-col">
                          <span className="flex items-center gap-1.5 truncate text-sm">
                            {p.display_name}
                            {p.custom && (
                              <span className="shrink-0 rounded-sm bg-[var(--color-accent-weak)] px-1 py-0.5 text-[9px] font-medium text-[var(--color-accent)]">
                                自分
                              </span>
                            )}
                          </span>
                          {/* 1行ティーザー（truncate＝1行で綺麗に省略。全文は「詳細」へ）。 */}
                          {p.description && (
                            <span className="truncate text-[11px] leading-snug text-[var(--color-ink-muted)]">
                              {p.description}
                            </span>
                          )}
                          {p.model && (
                            <span className="truncate font-mono text-[10px] text-[var(--color-ink-muted)]">
                              {p.model}
                            </span>
                          )}
                        </span>
                        {on && <Check size={15} className="shrink-0 self-center text-[var(--color-accent)]" />}
                      </button>
                      {/* 詳細トグル: 「この人はどんな人？」を開く。討論中(disabled)でも閲覧できるよう無効化しない。 */}
                      {detailText && (
                        <button
                          type="button"
                          onClick={() => toggleExpand(p.id)}
                          aria-expanded={expanded}
                          aria-controls={panelId}
                          aria-label={`${p.display_name} の詳細`}
                          title="この人の詳細"
                          className="flex shrink-0 items-center gap-0.5 self-stretch border-l border-[var(--color-line)] px-2 text-[10px] text-[var(--color-ink-muted)] transition-colors hover:text-[var(--color-accent)] focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[var(--color-accent)]"
                        >
                          詳細
                          <ChevronDown
                            size={12}
                            className={`transition-transform ${expanded ? "rotate-180" : ""}`}
                          />
                        </button>
                      )}
                    </div>
                    {expanded && detailText && (
                      <div
                        id={panelId}
                        className="border-t border-[var(--color-line)] px-3 py-2 text-[12px] leading-relaxed text-[var(--color-ink)] [overflow-wrap:anywhere]"
                      >
                        {detailText}
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        );
      })}
    </div>
  );
}
