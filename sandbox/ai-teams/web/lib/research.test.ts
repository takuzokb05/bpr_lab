// research.ts（splitBrief 等）と export.ts（buildMeetingMarkdown の調査結果セクション）の単体テスト。
// プロジェクトに専用テストランナーが無いため、tsc で JS に落として node で実行する素の assert で書く。
// 実行: web/ で `npx tsc lib/research.test.ts --outDir <tmp> ...` → `node <tmp>/lib/research.test.js`。

import assert from "node:assert/strict";
import { splitBrief } from "./research";
import { buildMeetingMarkdown, type ExportOptions } from "./export";
import type { Turn } from "./types";

let passed = 0;
function test(name: string, fn: () => void): void {
  fn();
  passed += 1;
  // eslint-disable-next-line no-console
  console.log(`  ok - ${name}`);
}

// (1) 「出典:」節ありの本文を findings / urls に分離できる（hadSourcesSection=true）。
test("splitBrief separates findings and urls on 出典: section", () => {
  const { findings, urls, hadSourcesSection } = splitBrief(
    "本文\n\n出典:\n- https://a.com\n- https://b.com",
  );
  assert.equal(findings, "本文");
  assert.deepEqual(urls, ["https://a.com", "https://b.com"]);
  assert.equal(hadSourcesSection, true, "出典節を分離できたら true");
});

// (2) 「出典:」節が無く本文中に素 URL がある場合は本文全体が findings、URL は本文から抽出。
// 別枠を出すと二重表示になるため hadSourcesSection=false（消費側は折り畳みを出さない）。
test("splitBrief keeps full body as findings and extracts inline urls", () => {
  const body = "詳細は https://example.com/page を参照。続きの本文。";
  const { findings, urls, hadSourcesSection } = splitBrief(body);
  assert.equal(findings, body);
  assert.deepEqual(urls, ["https://example.com/page"]);
  assert.equal(hadSourcesSection, false, "インライン URL のみなら false（二重表示回避）");
});

// (3) buildMeetingMarkdown: research turn 1件で調査結果セクションが details 折り畳み付きで出る。
test("buildMeetingMarkdown renders research with details fold", () => {
  const turns: Turn[] = [
    {
      turn_id: 1,
      speaker_id: "researcher",
      speaker_name: "調査役",
      content: "重要な発見の本文。\n\n出典:\n- https://a.com\n- https://b.com",
      phase: "research",
      round: 0,
      query: "テストクエリ",
    },
  ];
  const opts: ExportOptions = { summary: false, research: true, body: false };
  const md = buildMeetingMarkdown("テスト議題", turns, opts);

  assert.ok(md.includes("## 調査結果"), "見出し '## 調査結果' を含む");
  assert.ok(md.includes("### 「テストクエリ」"), "クエリ見出しを含む");
  assert.ok(md.includes("<details>"), "<details> 折り畳みを含む");
  assert.ok(md.includes("出典 2 件"), "出典 N 件のサマリを含む");

  // findings 本文は details の外（prose）に出る。
  const detailsIdx = md.indexOf("<details>");
  const findingsIdx = md.indexOf("重要な発見の本文。");
  assert.ok(findingsIdx >= 0, "findings 本文が出力に含まれる");
  assert.ok(findingsIdx < detailsIdx, "findings 本文は <details> より前（外）に出る");

  // URL は details の中（折り畳み）に出る。
  assert.ok(md.indexOf("https://a.com") > detailsIdx, "URL は <details> の中に出る");
});

// (4) opts.research=false なら調査結果セクションは出力されない。
test("buildMeetingMarkdown omits research section when opts.research=false", () => {
  const turns: Turn[] = [
    {
      turn_id: 1,
      speaker_id: "researcher",
      speaker_name: "調査役",
      content: "本文。\n\n出典:\n- https://a.com",
      phase: "research",
      round: 0,
      query: "q",
    },
  ];
  const opts: ExportOptions = { summary: false, research: false, body: false };
  const md = buildMeetingMarkdown("議題", turns, opts);
  assert.ok(!md.includes("## 調査結果"), "research=false で調査結果セクションは出ない");
  assert.ok(!md.includes("<details>"), "research=false で details も出ない");
});

// (5) 二重表示の番人: 出典見出しが無くインライン URL のみの調査本文は、export が <details> 別枠を
//     付けず URL を本文中に1回だけ出す（同一 URL が prose と折り畳みに二重表示される退行を防ぐ）。
test("buildMeetingMarkdown does not double-list inline urls without 出典 heading", () => {
  const turns: Turn[] = [
    {
      turn_id: 1,
      speaker_id: "researcher",
      speaker_name: "調査役",
      content: "詳細は https://only-once.com を参照。",
      phase: "research",
      round: 0,
      query: "q",
    },
  ];
  const md = buildMeetingMarkdown("議題", turns, { summary: false, research: true, body: false });
  assert.ok(!md.includes("<details>"), "出典見出し無しなら details 別枠を出さない");
  const occurrences = md.split("https://only-once.com").length - 1;
  assert.equal(occurrences, 1, `URL は本文中に1回だけ（二重表示しない）: ${occurrences}`);
});

// (6) UI/export 対称性: 両者は同一の splitBrief 結果を土台にする。専用 React ランナーが無いため、
//     共有純関数 splitBrief の出力が決定的であること＋export がその hadSourcesSection を尊重すること
//     （= true のとき details、false のとき非 details）を回帰として固定し、対称性の土台が崩れないことを守る。
test("UI/export share the same splitBrief contract", () => {
  const withHeading = "本文A\n\n出典:\n- https://a.com";
  const inlineOnly = "本文B https://b.com 続き";
  // splitBrief は決定的（同一入力→同一出力）。
  assert.deepEqual(splitBrief(withHeading), splitBrief(withHeading), "splitBrief は決定的");
  assert.equal(splitBrief(withHeading).hadSourcesSection, true);
  assert.equal(splitBrief(inlineOnly).hadSourcesSection, false);
  // export は flag を尊重: heading あり→details、inline のみ→details 無し。
  const mk = (c: string) =>
    buildMeetingMarkdown("t", [
      { turn_id: 1, speaker_id: "researcher", speaker_name: "調査役", content: c, phase: "research", round: 0, query: "q" },
    ], { summary: false, research: true, body: false });
  assert.ok(mk(withHeading).includes("<details>"), "heading あり→export は details を出す");
  assert.ok(!mk(inlineOnly).includes("<details>"), "inline のみ→export は details を出さない");
});

// eslint-disable-next-line no-console
console.log(`\nall ${passed} tests passed`);
