"use client";

import { useState } from "react";
import { createPreset } from "@/lib/api";
import type { Preset } from "@/lib/types";
import { X } from "lucide-react";

// id は name から素朴に slug 化（英数以外は _）。衝突は 409 をサーバが返す。
function slugify(name: string): string {
  return (
    name
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "") || `preset_${Date.now()}`
  );
}

export function PresetSaveDialog({
  personaIds,
  roundsPerPhase,
  redTeam,
  redTeamId,
  onClose,
  onSaved,
}: {
  personaIds: string[];
  roundsPerPhase: number;
  redTeam: boolean;
  redTeamId?: string | null;
  onClose: () => void;
  onSaved: (p: Preset) => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!name.trim()) {
      setError("名前を入力してください。");
      return;
    }
    setError(null);
    setSaving(true);
    try {
      const saved = await createPreset({
        id: slugify(name),
        name: name.trim(),
        description: description.trim() || undefined,
        persona_ids: personaIds,
        rounds_per_phase: roundsPerPhase,
        red_team: redTeam,
        red_team_id: redTeamId ?? null,
      });
      onSaved(saved);
    } catch (e) {
      // 409「preset id exists」/ 400「unknown persona ids…」等の detail を日本語文脈で提示。
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-[var(--color-ink)]/20"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="animate-turn-in relative w-[380px] max-w-[90vw] rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] p-5">
        <header className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium tracking-wide">現在の編成を保存</h2>
          <button
            onClick={onClose}
            className="text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
            aria-label="閉じる"
          >
            <X size={16} />
          </button>
        </header>

        {error && (
          <p className="mb-3 rounded-md border border-[var(--color-onair)] bg-[var(--color-paper)] px-3 py-2 text-xs text-[var(--color-onair)]">
            {error}
          </p>
        )}

        <label className="mb-3 flex flex-col gap-1">
          <span className="text-[11px] font-medium text-[var(--color-ink-muted)]">
            名前
          </span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例: 起業ブレスト"
            className="w-full rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-2.5 py-1.5 text-sm outline-none focus:border-[var(--color-accent)]"
          />
        </label>

        <label className="mb-4 flex flex-col gap-1">
          <span className="text-[11px] font-medium text-[var(--color-ink-muted)]">
            説明（任意）
          </span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full resize-y rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-2.5 py-1.5 text-sm outline-none focus:border-[var(--color-accent)]"
          />
        </label>

        <p className="mb-3 text-[11px] text-[var(--color-ink-muted)]">
          現在の {personaIds.length} 名・ラウンド {roundsPerPhase} を保存します。
        </p>

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={saving}
            className="rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm hover:border-[var(--color-ink-muted)] disabled:opacity-50"
          >
            キャンセル
          </button>
          <button
            onClick={submit}
            disabled={saving}
            className="rounded-md bg-[var(--color-accent)] px-4 py-1.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "保存中…" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}
