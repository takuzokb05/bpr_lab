"use client";

import { useState } from "react";
import { X, Plus, Trash2, Pencil } from "lucide-react";
import type { CustomPersona } from "@/lib/types";

const CATS: { id: CustomPersona["category"]; label: string }[] = [
  { id: "thinking", label: "思考" },
  { id: "founders", label: "経営者" },
  { id: "philosophers", label: "哲学者" },
];

// サーバの id pattern（^[a-z0-9_-]+$）に必ず合う id をブラウザ側で払い出す。
// 日本語名は slug 化できないので、衝突しない接頭辞付きの機械 id を使う（表示は display_name）。
function newId(): string {
  return `my-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

// 自分のペルソナ（クライアント定義）の作成・編集・削除。値の実体は page 側（localStorage）。
// 「このブラウザにのみ保存・サーバ非保存」を明記し、BYOK と同じ安心モデルにする。
export function MyPersonasDrawer({
  open,
  onClose,
  items,
  onSave,
  disabled,
}: {
  open: boolean;
  onClose: () => void;
  items: CustomPersona[];
  onSave: (list: CustomPersona[]) => void;
  disabled?: boolean;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [category, setCategory] = useState<CustomPersona["category"]>("thinking");
  const [desc, setDesc] = useState("");
  const [detailText, setDetailText] = useState("");
  const [prompt, setPrompt] = useState("");

  if (!open) return null;

  function resetForm() {
    setEditingId(null);
    setName("");
    setCategory("thinking");
    setDesc("");
    setDetailText("");
    setPrompt("");
  }

  function startEdit(p: CustomPersona) {
    setEditingId(p.id);
    setName(p.display_name);
    setCategory(p.category);
    setDesc(p.description ?? "");
    setDetailText(p.detail ?? "");
    setPrompt(p.system_prompt);
  }

  function save() {
    const display_name = name.trim();
    const system_prompt = prompt.trim();
    if (!display_name || !system_prompt) return;
    const description = desc.trim();
    const detail = detailText.trim();
    const id = editingId ?? newId();
    const next = items.filter((p) => p.id !== id);
    next.push({
      id,
      display_name,
      category,
      system_prompt,
      ...(description ? { description } : {}),
      ...(detail ? { detail } : {}),
    });
    onSave(next);
    resetForm();
  }

  function remove(id: string) {
    onSave(items.filter((p) => p.id !== id));
    if (editingId === id) resetForm();
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative flex h-full w-full max-w-md flex-col gap-4 overflow-y-auto border-l border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-5 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-sm tracking-wider">自分のペルソナ</h2>
          <button onClick={onClose} className="text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]">
            <X size={18} />
          </button>
        </div>

        <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
          作ったペルソナは<strong className="font-medium text-[var(--color-ink)]">このブラウザにのみ</strong>
          保存され、サーバには保存されません（討論時にその場だけ使われます）。司会・議長は自動で入るので、
          ここで作るのは<strong className="font-medium text-[var(--color-ink)]">議論する役（パネリスト）</strong>です。
        </p>

        {/* 一覧 */}
        {items.length > 0 && (
          <ul className="flex flex-col gap-1.5">
            {items.map((p) => (
              <li
                key={p.id}
                className="flex items-center justify-between gap-2 rounded-md border border-[var(--color-line)] px-2.5 py-1.5"
              >
                <span className="flex min-w-0 flex-col">
                  <span className="truncate text-sm text-[var(--color-ink)]">{p.display_name}</span>
                  <span className="truncate text-[10px] text-[var(--color-ink-muted)]">
                    {CATS.find((c) => c.id === p.category)?.label}
                  </span>
                </span>
                <span className="flex shrink-0 gap-1">
                  <button
                    onClick={() => startEdit(p)}
                    disabled={disabled}
                    className="rounded p-1 text-[var(--color-ink-muted)] hover:text-[var(--color-accent)] disabled:opacity-40"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => remove(p.id)}
                    disabled={disabled}
                    className="rounded p-1 text-[var(--color-ink-muted)] hover:text-[var(--color-onair)] disabled:opacity-40"
                  >
                    <Trash2 size={14} />
                  </button>
                </span>
              </li>
            ))}
          </ul>
        )}

        {/* フォーム */}
        <div className="flex flex-col gap-2 border-t border-[var(--color-line)] pt-4">
          <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
            {editingId ? "編集" : "新規作成"}
          </span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="名前（例: 投資家 / 現場の看護師 / 孫子）"
            disabled={disabled}
            className="rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-2.5 py-1.5 text-sm outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
          />
          <input
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="一行説明（任意・例: 数字でリターンを問う投資家）"
            disabled={disabled}
            className="rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-2.5 py-1.5 text-sm outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
          />
          <textarea
            value={detailText}
            onChange={(e) => setDetailText(e.target.value)}
            placeholder="詳細説明（任意・「詳細」ボタンで開く。どんな人か・何が持ち味か）"
            rows={2}
            disabled={disabled}
            className="resize-y rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-2.5 py-1.5 text-sm leading-relaxed outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
          />
          <div className="flex rounded-md border border-[var(--color-line)] p-0.5">
            {CATS.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setCategory(c.id)}
                disabled={disabled}
                className={`flex-1 rounded px-2 py-1 text-[11px] transition-colors disabled:opacity-50 ${
                  category === c.id
                    ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
                    : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="人格・判断軸・口調を書く（例: あなたは投資家。常にリターンと回収期間を問い、感情論を数字に引き戻す…）"
            rows={6}
            disabled={disabled}
            className="resize-y rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-2.5 py-2 text-sm leading-relaxed outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
          />
          <div className="flex gap-2">
            <button
              onClick={save}
              disabled={disabled || !name.trim() || !prompt.trim()}
              className="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              <Plus size={14} /> {editingId ? "更新" : "追加"}
            </button>
            {editingId && (
              <button
                onClick={resetForm}
                className="rounded-md px-3 py-1.5 text-xs text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
              >
                取消
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
