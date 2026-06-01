// 絵文字アバターの置き換え：カテゴリ色の円にモノグラム（頭文字）を白で。

export function Avatar({
  monogram,
  accent,
  size = 36,
  active = false,
}: {
  monogram: string;
  accent: string;
  size?: number;
  active?: boolean;
}) {
  return (
    <span
      className="inline-flex shrink-0 items-center justify-center rounded-full font-medium text-white select-none"
      style={{
        width: size,
        height: size,
        backgroundColor: accent,
        fontSize: size * 0.4,
        boxShadow: active ? `0 0 0 3px ${accent}33` : undefined,
      }}
      aria-hidden="true"
    >
      {monogram}
    </span>
  );
}
