// 調査ブリーフ本文のパース（出典 URL 抽出・本文/出典の分離）。React 非依存の純関数で、
// UI（ResearchNotes）とエクスポート（export.ts）の両方から使う。「出典:」見出しの文言・改行形式は
// Python 側（core/context.py, core/llm_client.py）との凍結契約なので変更しないこと。

// 調査ブリーフ本文から出典 URL を拾う（「出典:」節に限らず本文中の素 URL も拾う）。
export const URL_RE = /https?:\/\/[^\s)>\]）」]+/g;

export function extractUrls(text: string): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const m of (text ?? "").matchAll(URL_RE)) {
    // 末尾の句読点・閉じ括弧・Markdown 装飾記号(** _ ~ 等)を URL から外す。本文プローズ中に
    // モデルが **https://...** のように装飾付きで書いた素 URL を壊れた href にしないため。
    const u = m[0].replace(/[.,;:!?。、，；：！？)\]）」』】>*_~"'`]+$/u, "");
    if (!seen.has(u)) {
      seen.add(u);
      out.push(u);
    }
  }
  return out;
}

export function hostOf(u: string): string {
  try {
    return new URL(u).hostname.replace(/^www\./, "");
  } catch {
    return u;
  }
}

// 調査ブリーフを「本文（findings）」と「出典 URL」に分ける。web_research は末尾に
// "出典:\n- url..." を付けるので、そこで割って本文に出典を二重表示しない（ソースは折り畳みへ）。
// hadSourcesSection=true は「出典節を本文から切り出せた＝findings に URL が残っていない」ことを示す。
// 消費側（UI/export）はこのフラグが true のときだけ別枠の出典折り畳みを出す（false＝URL は本文中に
// インラインで残るため、別枠を足すと同一 URL が二重表示になる）。
export function splitBrief(content: string): {
  findings: string;
  urls: string[];
  hadSourcesSection: boolean;
} {
  const text = content ?? "";
  const m = text.match(/(?:^|\n)\s*出典[:：]\s*\n/);
  if (m && m.index !== undefined) {
    const before = text.slice(0, m.index).trim();
    const urls = extractUrls(text.slice(m.index));
    // 出典節の前に本文がある通常ケース＝本文は URL を含まないので別枠を出してよい。
    if (before) {
      return { findings: before, urls: urls.length ? urls : extractUrls(text), hadSourcesSection: true };
    }
    // 見出しはあるが前段本文が空 → 全文を本文にし、二重表示回避のため別枠は出さない。
    return { findings: text.trim(), urls: extractUrls(text), hadSourcesSection: false };
  }
  // 出典見出し無し＝URL は本文中インライン。別枠は出さない（消費側で二重表示を防ぐ）。
  return { findings: text.trim(), urls: extractUrls(text), hadSourcesSection: false };
}
