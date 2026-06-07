// 会議結果（討論）の書き出し。手持ちの LLM にそのまま投げられる素の Markdown を作る。
// セクション（要約 / 調査結果 / 会議内容）はチェックボックスで取捨選択し、1ファイルにまとめる。

import { type Turn, PHASE_LABELS } from "./types";
import { splitBrief } from "./research";

export interface ExportOptions {
  summary: boolean; // 要約（議長の議事録 = synthesis）
  research: boolean; // 調査結果（調査役 researcher のブリーフ）
  body: boolean; // 会議内容（発言の全文ログ）
}

function phaseLabel(phase: string): string {
  return PHASE_LABELS[phase] ?? phase;
}

function isResearch(t: Turn): boolean {
  return t.speaker_id === "researcher" || t.phase === "research";
}

function isBody(t: Turn): boolean {
  // 本編＝議事録/要約/調査メモを除いた発言（人間の追い質問は含む）。
  return (
    t.phase !== "synthesis" &&
    t.phase !== "summary" &&
    !isResearch(t)
  );
}

// 各セクションに中身があるか（チェックボックスの有効/無効に使う）。
export function sectionAvailability(turns: Turn[]): ExportOptions {
  return {
    summary: turns.some((t) => t.phase === "synthesis" && (t.content ?? "").trim().length > 0),
    research: turns.some((t) => isResearch(t) && (t.content ?? "").trim().length > 0),
    body: turns.some((t) => isBody(t) && (t.content ?? "").trim().length > 0),
  };
}

/**
 * 討論を Markdown 1枚に組み立てる。読みやすさと LLM 投入のしやすさを優先し、
 * 要約（TL;DR）→ 調査結果（事実）→ 会議内容（全文ログ）の順にする。
 * opts で選ばれ、かつ中身のあるセクションだけを出す。
 */
export function buildMeetingMarkdown(
  topic: string,
  turns: Turn[],
  opts: ExportOptions
): string {
  const blocks: string[] = [];
  blocks.push(`# ${topic.trim() || "AI討論"}`);

  // 参加者（発言したパネリスト。調査役・人間は除く・重複なし）。
  const speakers = Array.from(
    new Set(
      turns
        .filter((t) => !isResearch(t) && t.phase !== "human")
        .map((t) => t.speaker_name)
        .filter(Boolean)
    )
  );
  if (speakers.length) blocks.push(`参加者: ${speakers.join(" / ")}`);

  // 議事録は close 毎に追記され複数あり得る。書き出しは**最新**を採る（作り直しを反映）。
  const synthesisAll = turns.filter((t) => t.phase === "synthesis");
  const synthesis = synthesisAll.length ? synthesisAll[synthesisAll.length - 1] : undefined;
  const research = turns.filter((t) => isResearch(t) && (t.content ?? "").trim());
  const body = turns.filter((t) => isBody(t) && (t.content ?? "").trim());

  if (opts.summary && synthesis && synthesis.content.trim()) {
    blocks.push(`## 議事録`);
    blocks.push(synthesis.content.trim());
  }

  if (opts.research && research.length) {
    blocks.push(`## 調査結果`);
    for (const t of research) {
      if (t.query) blocks.push(`### 「${t.query}」`);
      // 本文（findings）と出典 URL を分離。UI（ResearchNotes）と同じ splitBrief を使い、
      // 出典は <details> 折り畳みに圧縮する（URL は全件保持＝不可逆な hostname 圧縮はしない）。
      const { findings, urls, hadSourcesSection } = splitBrief(t.content);
      blocks.push(findings);
      // 出典節を分離できたときだけ折り畳みを足す（インライン URL の二重表示を避ける）。
      if (hadSourcesSection && urls.length) {
        const list = urls.map((u) => `- ${u}`).join("\n");
        blocks.push(`<details>\n<summary>出典 ${urls.length} 件</summary>\n\n${list}\n</details>`);
      }
    }
  }

  if (opts.body && body.length) {
    blocks.push(`## 会議内容`);
    for (const t of body) {
      const who = t.phase === "human" ? "あなた" : t.speaker_name;
      blocks.push(`### ${who}（${phaseLabel(t.phase)}）`);
      blocks.push(t.content.trim());
    }
  }

  return blocks.join("\n\n").trim() + "\n";
}

// 議題と日付からファイル名を作る（OS で禁止される文字を除去）。
export function meetingFilename(topic: string): string {
  const base =
    (topic || "ai-council")
      .replace(/[\\/:*?"<>|\n\r\t]+/g, " ")
      .trim()
      .slice(0, 40) || "ai-council";
  const d = new Date();
  const ymd = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(
    d.getDate()
  ).padStart(2, "0")}`;
  return `${base}_${ymd}.md`;
}

// クリップボードへコピー。Clipboard API（要 secure context）→ 失敗時は textarea + execCommand に退避。
export async function copyText(text: string): Promise<boolean> {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* フォールバックへ */
  }
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.top = "-1000px";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}

// Markdown を .md ファイルとしてダウンロードさせる。
export function downloadMarkdown(filename: string, md: string): void {
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  // revoke は少し遅らせる（即時だと一部ブラウザでダウンロードが中断する）。
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
