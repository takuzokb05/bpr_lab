"use client";

import { useState } from "react";
import {
  CATEGORY_LABELS,
  type Persona,
  type PersonaCategory,
  type PersonaDetail,
} from "@/lib/types";
import { createPersona, updatePersona } from "@/lib/api";
import { Avatar } from "./Avatar";

const CATEGORIES: PersonaCategory[] = [
  "facilitation",
  "thinking",
  "founders",
  "philosophers",
  "chair",
  "scribe",
];

// display_name → モノグラム（core/personas.py の規則に寄せた軽量版・プレビュー用）。
function previewMonogram(name: string): string {
  const words = name.replace("　", " ").trim().split(/\s+/);
  if (words.length >= 2 && /^[\x00-\x7F]/.test(words[0]) && /^[\x00-\x7F]/.test(words[1])) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  const base = name.split("（")[0].split("(")[0].trim();
  return base.slice(0, 1) || "?";
}

const HEX = /^#[0-9a-fA-F]{6}$/;

export function PersonaForm({
  initial,
  onSaved,
  onCancel,
}: {
  // 既存編集なら詳細を、新規なら null。
  initial: PersonaDetail | null;
  onSaved: (p: Persona) => void;
  onCancel: () => void;
}) {
  const isEdit = initial !== null;

  const [id, setId] = useState(initial?.id ?? "");
  const [displayName, setDisplayName] = useState(initial?.display_name ?? "");
  const [category, setCategory] = useState<PersonaCategory>(
    initial?.category ?? "thinking"
  );
  const [description, setDescription] = useState(initial?.description ?? "");
  const [detail, setDetail] = useState(initial?.detail ?? "");
  const [systemPrompt, setSystemPrompt] = useState(initial?.system_prompt ?? "");
  const [temperature, setTemperature] = useState(
    initial?.temperature != null ? String(initial.temperature) : ""
  );
  const [model, setModel] = useState(initial?.model ?? "");
  const [tags, setTags] = useState((initial?.tags ?? []).join(", "));
  const [speaks, setSpeaks] = useState(initial?.speaks ?? true);
  const [accent, setAccent] = useState(initial?.accent ?? "#5B7C8A");

  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // クライアント一次検証（サーバ検証の前段で素早くフィードバック）。
  function validate(): string | null {
    if (!id.trim()) return "ID は必須です。";
    if (!/^[a-z0-9_]+$/.test(id.trim()))
      return "ID は半角英小文字・数字・アンダースコアで入力してください。";
    if (!displayName.trim()) return "表示名は必須です。";
    if (!systemPrompt.trim()) return "システムプロンプトは必須です。";
    if (accent && !HEX.test(accent)) return "アクセント色は #RRGGBB 形式で入力してください。";
    if (temperature.trim()) {
      const t = Number(temperature);
      if (Number.isNaN(t) || t < 0 || t > 2)
        return "temperature は 0〜2 の数値で入力してください。";
    }
    return null;
  }

  async function submit() {
    const v = validate();
    if (v) {
      setError(v);
      return;
    }
    setError(null);
    setSaving(true);
    const body: Record<string, unknown> = {
      id: id.trim(),
      display_name: displayName.trim(),
      category,
      system_prompt: systemPrompt,
      speaks,
      accent: accent.trim(),
      tags: tags
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };
    if (model.trim()) body.model = model.trim();
    if (temperature.trim()) body.temperature = Number(temperature);
    if (description.trim()) body.description = description.trim();
    if (detail.trim()) body.detail = detail.trim();
    // 因縁（relationships）は専用 UI を持たないが、編集保存で消さないよう既存値を round-trip する。
    if (initial?.relationships?.length) body.relationships = initial.relationships;

    try {
      const saved = isEdit
        ? await updatePersona(id.trim(), body)
        : await createPersona(body);
      onSaved(saved);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  const monogram = previewMonogram(displayName || id || "?");
  const previewAccent = HEX.test(accent) ? accent : "#5B7C8A";

  return (
    <div className="flex flex-col gap-4">
      {/* ライブプレビュー */}
      <div className="flex items-center gap-3 rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2.5">
        <Avatar monogram={monogram} accent={previewAccent} size={36} />
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">
            {displayName || "（表示名）"}
          </p>
          <p className="text-[11px] text-[var(--color-ink-muted)]">
            {CATEGORY_LABELS[category]}
          </p>
        </div>
      </div>

      {error && (
        <p className="rounded-md border border-[var(--color-onair)] bg-[var(--color-paper)] px-3 py-2 text-xs text-[var(--color-onair)]">
          {error}
        </p>
      )}

      <Field label="ID（半角英小文字・数字・_）">
        <input
          value={id}
          onChange={(e) => setId(e.target.value)}
          disabled={isEdit}
          placeholder="例: my_advisor"
          className={inputCls + (isEdit ? " opacity-60" : "")}
        />
      </Field>

      <Field label="表示名">
        <input
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="例: 私の参謀"
          className={inputCls}
        />
      </Field>

      <Field label="カテゴリ">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value as PersonaCategory)}
          className={inputCls}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {CATEGORY_LABELS[c]}
            </option>
          ))}
        </select>
      </Field>

      <Field label="一行説明（任意・カードのティーザー）">
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="例: 根拠と数字で筋を通し、論理の穴を突く番人。"
          className={inputCls}
        />
      </Field>

      <Field label="詳細説明（任意・「詳細」で開く。偉人なら何をした人かも）">
        <textarea
          value={detail}
          onChange={(e) => setDetail(e.target.value)}
          rows={3}
          placeholder="例: 会議における論理の番人。主張の根拠と数字を求め、感情だけの合意を許さず、検証可能な論点へ整理し直す役。"
          className={inputCls + " resize-y leading-relaxed"}
        />
      </Field>

      <Field label="システムプロンプト">
        <textarea
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          rows={6}
          placeholder="このペルソナの判断軸・口調・役割を書きます。"
          className={inputCls + " resize-y leading-relaxed"}
        />
      </Field>

      <div className="grid grid-cols-2 gap-3">
        <Field label="temperature（任意・0〜2）">
          <input
            value={temperature}
            onChange={(e) => setTemperature(e.target.value)}
            placeholder="既定"
            className={inputCls}
          />
        </Field>
        <Field label="アクセント色（#RRGGBB）">
          <div className="flex items-center gap-2">
            <input
              value={accent}
              onChange={(e) => setAccent(e.target.value)}
              className={inputCls + " font-mono"}
            />
            <span
              className="inline-block h-7 w-7 shrink-0 rounded-md border border-[var(--color-line)]"
              style={{ backgroundColor: previewAccent }}
              aria-hidden="true"
            />
          </div>
        </Field>
      </div>

      <Field label="モデル（任意・空でエンジン既定）">
        <input
          value={model}
          onChange={(e) => setModel(e.target.value)}
          placeholder="例: claude-sonnet-4-20250514"
          className={inputCls + " font-mono"}
        />
      </Field>

      <Field label="タグ（カンマ区切り）">
        <input
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="例: product, vision"
          className={inputCls}
        />
      </Field>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={speaks}
          onChange={(e) => setSpeaks(e.target.checked)}
        />
        発言ローテーションに参加する（書記など記録専任は外す）
      </label>

      <div className="flex justify-end gap-2 pt-1">
        <button
          onClick={onCancel}
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
          {saving ? "保存中…" : isEdit ? "更新" : "作成"}
        </button>
      </div>
    </div>
  );
}

const inputCls =
  "w-full rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-2.5 py-1.5 text-sm outline-none focus:border-[var(--color-accent)]";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] font-medium text-[var(--color-ink-muted)]">
        {label}
      </span>
      {children}
    </label>
  );
}
