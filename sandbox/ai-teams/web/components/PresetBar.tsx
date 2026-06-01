"use client";

import { useMemo } from "react";
import type { Persona, Preset } from "@/lib/types";
import { Save, AlertTriangle } from "lucide-react";

// 編成プリセットのバー。選択して適用 / 現在の編成を保存する。
// プリセットの persona_ids に未知 id が混じる（valid:false）場合は警告を出す。
export function PresetBar({
  presets,
  personas,
  selectedPresetId,
  onApply,
  onSaveCurrent,
  disabled,
}: {
  presets: Preset[];
  personas: Persona[];
  selectedPresetId: string | null;
  onApply: (preset: Preset | null) => void;
  onSaveCurrent: () => void;
  disabled: boolean;
}) {
  const knownIds = useMemo(() => new Set(personas.map((p) => p.id)), [personas]);

  const current = presets.find((p) => p.id === selectedPresetId) ?? null;
  // 適用中プリセットに、いま存在しないペルソナが含まれていないか。
  const missing = current
    ? current.persona_ids.filter((id) => !knownIds.has(id))
    : [];

  return (
    <div className="mb-5 flex flex-col gap-2">
      <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
        プリセット
      </h2>
      <div className="flex items-center gap-2">
        <select
          value={selectedPresetId ?? ""}
          onChange={(e) => {
            const id = e.target.value;
            onApply(id ? (presets.find((p) => p.id === id) ?? null) : null);
          }}
          disabled={disabled}
          className="min-w-0 flex-1 rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-2.5 py-1.5 text-sm outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
        >
          <option value="">手動で編成</option>
          {presets.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
              {p.builtin ? "（同梱）" : ""}
            </option>
          ))}
        </select>
        <button
          onClick={onSaveCurrent}
          disabled={disabled}
          title="現在の編成を保存"
          aria-label="現在の編成を保存"
          className="flex shrink-0 items-center gap-1 rounded-md border border-[var(--color-line)] px-2.5 py-1.5 text-xs text-[var(--color-ink-muted)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] disabled:opacity-50"
        >
          <Save size={13} /> 保存
        </button>
      </div>

      {current?.description && (
        <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
          {current.description}
        </p>
      )}

      {missing.length > 0 && (
        <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-[var(--color-onair)]">
          <AlertTriangle size={13} className="mt-0.5 shrink-0" />
          <span>
            このプリセットには存在しないペルソナが含まれています（{missing.join(", ")}）。
            該当分は編成から除外されます。
          </span>
        </p>
      )}
    </div>
  );
}
