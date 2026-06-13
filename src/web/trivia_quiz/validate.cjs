/*
 * 問題データの検証スクリプト
 *   実行: node src/web/trivia_quiz/validate.cjs
 * questions/ 配下の全データを読み込み、形式の不備と id の重複を検査する。
 * 問題を追加・編集したら、これを通してからコミットすると安全。
 */
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const dir = path.join(__dirname, "questions");
const files = ["_categories.js", "it.js", "life.js", "culture.js"];

const ctx = { window: {} };
vm.createContext(ctx);
for (const f of files) {
  vm.runInContext(fs.readFileSync(path.join(dir, f), "utf8"), ctx, { filename: f });
}
const { CATEGORIES, QUIZ_DATA } = vm.runInContext("({CATEGORIES,QUIZ_DATA})", ctx);

function hashId(s) {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h) ^ s.charCodeAt(i);
  return (h >>> 0).toString(36);
}

const errors = [];
const ids = new Map();
QUIZ_DATA.forEach((q, i) => {
  const where = `#${i} (${q.category}) "${(q.question || "").slice(0, 24)}…"`;
  if (!CATEGORIES[q.category]) errors.push(`${where}: 未定義のカテゴリ ${q.category}`);
  if (!q.qual) errors.push(`${where}: qual が空`);
  if (!Array.isArray(q.choices) || q.choices.length !== 4)
    errors.push(`${where}: choices は4つ必要`);
  if (!(Number.isInteger(q.answer) && q.answer >= 0 && q.answer <= 3))
    errors.push(`${where}: answer は0〜3`);
  ["conclusion", "why", "useful"].forEach((k) => {
    if (!q.explanation || !q.explanation[k]) errors.push(`${where}: explanation.${k} が空`);
  });
  const id = q.id || hashId(q.category + "|" + q.question);
  if (ids.has(id)) errors.push(`${where}: id 重複（${ids.get(id)} と同じ問題文の可能性）`);
  else ids.set(id, where);
});

const byCat = {};
QUIZ_DATA.forEach((q) => (byCat[q.category] = (byCat[q.category] || 0) + 1));

console.log(`合計 ${QUIZ_DATA.length} 問`);
Object.entries(byCat).forEach(([c, n]) => console.log(`  ${c}: ${n} 問`));

if (errors.length) {
  console.error(`\n❌ ${errors.length} 件の問題:`);
  errors.forEach((e) => console.error("  - " + e));
  process.exit(1);
}
console.log("\n✅ すべて妥当です");
