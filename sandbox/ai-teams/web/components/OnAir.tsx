"use client";

// 報道番組の「ON AIR」表示。running のときだけ赤ドット＋小ラベルで点灯（小面積限定）。
// それ以外の状態は無彩色テキストで静かに示す（黒ベタ・絵文字・影は使わない）。

type Status = "idle" | "running" | "paused" | "done" | "error";

export function OnAir({ status }: { status: Status }) {
  if (status === "running") {
    return (
      <span className="flex items-center gap-1.5">
        <span
          className="animate-onair-breathe inline-block h-2 w-2 rounded-full"
          style={{ backgroundColor: "var(--color-onair)" }}
          aria-hidden="true"
        />
        <span
          className="text-[11px] font-medium uppercase tracking-widest"
          style={{ color: "var(--color-onair)" }}
        >
          ON AIR
        </span>
      </span>
    );
  }

  const labels: Record<Exclude<Status, "running">, string> = {
    idle: "待機中",
    paused: "一時停止",
    done: "完了",
    error: "中断",
  };

  return (
    <span className="text-[11px] tracking-wider text-[var(--color-ink-muted)]">
      {labels[status]}
    </span>
  );
}
