"use client";

import { X, Trash2, MessageSquareText } from "lucide-react";
import type { HistoryEntry } from "@/lib/config";

const STATUS_LABEL: Record<string, string> = {
  running: "進行中",
  paused: "議場開放",
  done: "完了",
  error: "エラー",
};

function fmt(ms: number): string {
  try {
    return new Date(ms).toLocaleString("ja-JP", {
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

// 討論履歴（このブラウザに保存された transcript）。見返し・再開の入口。
export function HistoryDrawer({
  open,
  onClose,
  entries,
  onOpen,
  onDelete,
  currentId,
}: {
  open: boolean;
  onClose: () => void;
  entries: HistoryEntry[];
  onOpen: (entry: HistoryEntry) => void;
  onDelete: (id: string) => void;
  currentId: string | null;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative flex h-full w-full max-w-md flex-col gap-3 overflow-y-auto border-l border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-5 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-sm tracking-wider">討論履歴</h2>
          <button onClick={onClose} className="text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]">
            <X size={18} />
          </button>
        </div>
        <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
          討論は<strong className="font-medium text-[var(--color-ink)]">このブラウザにのみ</strong>
          記録されます（サーバ非保存）。クリックで見返し、進行中だったものは再開を試みます。
        </p>

        {entries.length === 0 ? (
          <p className="mt-4 text-xs text-[var(--color-ink-muted)]">まだ履歴はありません。</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {entries.map((e) => (
              <li
                key={e.id}
                className={`flex items-center gap-2 rounded-md border px-2.5 py-2 ${
                  e.id === currentId
                    ? "border-[var(--color-accent)] bg-[var(--color-accent-weak)]"
                    : "border-[var(--color-line)]"
                }`}
              >
                <button
                  onClick={() => onOpen(e)}
                  className="flex min-w-0 flex-1 items-start gap-2 text-left"
                >
                  <MessageSquareText size={15} className="mt-0.5 shrink-0 text-[var(--color-ink-muted)]" />
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate text-sm text-[var(--color-ink)]">{e.topic}</span>
                    <span className="truncate text-[10px] text-[var(--color-ink-muted)]">
                      {fmt(e.updatedAt)}・{STATUS_LABEL[e.status] ?? e.status}・{e.turns.length} 発言
                    </span>
                  </span>
                </button>
                <button
                  onClick={() => onDelete(e.id)}
                  className="shrink-0 rounded p-1 text-[var(--color-ink-muted)] hover:text-[var(--color-onair)]"
                  title="削除"
                >
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
