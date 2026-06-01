"use client";

import { CATEGORY_LABELS, type Persona, type PersonaCategory } from "@/lib/types";
import { Avatar } from "./Avatar";
import { Check } from "lucide-react";

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
}: {
  personas: Persona[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  disabled: boolean;
}) {
  const groups = CATEGORY_ORDER.map((cat) => ({
    cat,
    items: personas.filter((p) => p.category === cat),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
          編成
        </h2>
        <p className="mt-1 text-xs text-[var(--color-ink-muted)]">
          {selected.size} 名を選択中
        </p>
      </div>

      {groups.map((g) => (
        <div key={g.cat} className="flex flex-col gap-1.5">
          <h3 className="text-[11px] font-medium text-[var(--color-ink-muted)]">
            {CATEGORY_LABELS[g.cat]}
          </h3>
          {g.items.map((p) => {
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
      ))}
    </div>
  );
}
