"use client";

import { useEffect, useState } from "react";
import { CATEGORY_LABELS, type Persona, type PersonaDetail } from "@/lib/types";
import { deletePersona, fetchPersonaDetail } from "@/lib/api";
import { PersonaForm } from "./PersonaForm";
import { Avatar } from "./Avatar";
import { X, Plus, Copy, Trash2, Pencil } from "lucide-react";

type Mode =
  | { kind: "list" }
  | { kind: "new"; initial: PersonaDetail | null }
  | { kind: "edit"; initial: PersonaDetail };

export function PersonaManagerDrawer({
  open,
  personas,
  onClose,
  onChanged,
}: {
  open: boolean;
  personas: Persona[];
  onClose: () => void;
  // CRUD 後に親が一覧を再取得するためのフック。
  onChanged: () => void;
}) {
  const [mode, setMode] = useState<Mode>({ kind: "list" });
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 閉じたら一覧モードに戻す。
  useEffect(() => {
    if (!open) setMode({ kind: "list" });
  }, [open]);

  if (!open) return null;

  async function startEdit(id: string) {
    setError(null);
    try {
      const detail = await fetchPersonaDetail(id);
      setMode({ kind: "edit", initial: detail });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  // 複製: 詳細を取り、id を空にして「新規」フォームへ流し込む。
  async function startDuplicate(id: string) {
    setError(null);
    try {
      const detail = await fetchPersonaDetail(id);
      setMode({
        kind: "new",
        initial: { ...detail, id: "", display_name: `${detail.display_name}（複製）` },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function remove(id: string) {
    setError(null);
    setBusyId(id);
    try {
      await deletePersona(id);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      {/* 背景オーバーレイ（無彩色・控えめ） */}
      <div
        className="absolute inset-0 bg-[var(--color-ink)]/20"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="animate-chyron-in relative flex h-full w-[420px] max-w-full flex-col border-l border-[var(--color-line)] bg-[var(--color-surface)]">
        <header className="flex items-center justify-between border-b border-[var(--color-line)] px-5 py-3">
          <h2 className="text-sm font-medium tracking-wide">
            {mode.kind === "list"
              ? "ペルソナ管理"
              : mode.kind === "edit"
                ? "ペルソナを編集"
                : "ペルソナを追加"}
          </h2>
          <button
            onClick={onClose}
            className="text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
            aria-label="閉じる"
          >
            <X size={16} />
          </button>
        </header>

        {error && (
          <p className="mx-5 mt-3 rounded-md border border-[var(--color-onair)] bg-[var(--color-paper)] px-3 py-2 text-xs text-[var(--color-onair)]">
            {error}
          </p>
        )}

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          {mode.kind === "list" ? (
            <div className="flex flex-col gap-2">
              <button
                onClick={() => setMode({ kind: "new", initial: null })}
                className="mb-1 flex items-center justify-center gap-1.5 rounded-md border border-dashed border-[var(--color-line)] px-3 py-2 text-sm text-[var(--color-ink-muted)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
              >
                <Plus size={14} /> 新しいペルソナ
              </button>
              {personas.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center gap-3 rounded-md border border-[var(--color-line)] px-2.5 py-2"
                >
                  <Avatar monogram={p.monogram} accent={p.accent} size={30} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm">{p.display_name}</p>
                    <p className="text-[11px] text-[var(--color-ink-muted)]">
                      {CATEGORY_LABELS[p.category]}
                    </p>
                  </div>
                  <button
                    onClick={() => startEdit(p.id)}
                    className="p-1 text-[var(--color-ink-muted)] hover:text-[var(--color-accent)]"
                    aria-label="編集"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => startDuplicate(p.id)}
                    className="p-1 text-[var(--color-ink-muted)] hover:text-[var(--color-accent)]"
                    aria-label="複製"
                  >
                    <Copy size={14} />
                  </button>
                  <button
                    onClick={() => remove(p.id)}
                    disabled={busyId === p.id}
                    className="p-1 text-[var(--color-ink-muted)] hover:text-[var(--color-onair)] disabled:opacity-40"
                    aria-label="削除"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <PersonaForm
              initial={mode.initial}
              onSaved={() => {
                onChanged();
                setMode({ kind: "list" });
              }}
              onCancel={() => setMode({ kind: "list" })}
            />
          )}
        </div>
      </div>
    </div>
  );
}
