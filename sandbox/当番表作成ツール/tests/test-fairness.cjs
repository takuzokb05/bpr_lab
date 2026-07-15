/**
 * 回数公平性テスト — 実データ（当番表データ_2026年4月.json）を使い、
 * 既存割り当てをクリアして自動割り当てを実行、回数偏差を検証する
 *
 * 使い方: node tests/test-fairness.cjs
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const HTML_PATH = path.resolve(__dirname, '../src/当番表作成ツール-v2.html');
const DATA_PATH = path.resolve(__dirname, '当番表データ_2026年4月.json');

// 実データ読み込み、割り当てをクリアして自動割り当てをテスト
const TEST_DATA = JSON.parse(fs.readFileSync(DATA_PATH, 'utf-8'));
TEST_DATA.assignments = {}; // 既存割り当てをクリア

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function runTest() {
  console.log('=== 回数公平性テスト（30人、制約混在） ===\n');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox'],
    protocolTimeout: 120000,
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });

  const fileUrl = `file://${HTML_PATH.replace(/\\/g, '/')}`;
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });

  // localStorageクリア → テストデータ投入
  await page.evaluate(() => localStorage.clear());
  await page.evaluate((data) => {
    localStorage.setItem('toban_tool_data', JSON.stringify(data));
  }, TEST_DATA);
  await page.reload({ waitUntil: 'networkidle0' });
  await wait(500);

  // 自動割り当て実行
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('.btn-success');
    for (const btn of buttons) {
      if (btn.textContent.includes('自動割り当て')) {
        btn.click();
        return;
      }
    }
  });
  await wait(2000);

  // 結果を取得
  const result = await page.evaluate(() => {
    const data = JSON.parse(localStorage.getItem('toban_tool_data'));
    if (!data || !data.assignments) return null;

    // 回数集計
    const counts = {};
    for (const s of data.staff) counts[s.id] = 0;
    for (const dateKey of Object.keys(data.assignments)) {
      const daySlots = data.assignments[dateKey];
      for (const slotId of Object.keys(daySlots)) {
        for (const id of (daySlots[slotId] || [])) {
          counts[id] = (counts[id] || 0) + 1;
        }
      }
    }

    // 制約情報付きで返す
    return data.staff.map(s => {
      const constraints = [];
      if (s.shortTime) constraints.push(`時短(${s.shortTime.start}-${s.shortTime.end})`);
      if (s.dayOffWeekdays && s.dayOffWeekdays.length > 0) constraints.push(`公休${s.dayOffWeekdays.length}日/週`);
      if (s.unavailableDates && s.unavailableDates.length > 0) constraints.push(`不可${s.unavailableDates.length}日`);
      if (s.fixedDays && s.fixedDays.length > 0) constraints.push(`固定枠${s.fixedDays.length}件`);
      if (s.exemptFromDate) constraints.push(`免除(${s.exemptFromDate}~)`);
      return {
        name: s.name,
        count: counts[s.id] || 0,
        weight: s.dutyWeight ?? 1,
        exempt: !!s.exemptFromDate,
        constraints: constraints.length > 0 ? constraints.join(', ') : '制約なし',
      };
    });
  });

  await browser.close();

  if (!result) {
    console.error('割り当て結果が取得できませんでした');
    process.exit(1);
  }

  // dutyWeightグループ別に分析
  const groups = { high: [], normal: [], low: [], exempt: [] };
  for (const r of result) {
    if (r.exempt) groups.exempt.push(r);
    else if (r.weight >= 1.5) groups.high.push(r);
    else if (r.weight <= 0.5) groups.low.push(r);
    else groups.normal.push(r);
  }

  const activeResult = result.filter(r => !r.exempt && r.weight > 0);
  const allCounts = activeResult.map(r => r.count);
  const avg = allCounts.reduce((a, b) => a + b, 0) / allCounts.length;
  const max = Math.max(...allCounts);
  const min = Math.min(...allCounts);
  const stdDev = Math.sqrt(allCounts.reduce((sum, c) => sum + (c - avg) ** 2, 0) / allCounts.length);

  const printGroup = (label, list) => {
    if (list.length === 0) return;
    console.log(`\n--- ${label} (${list.length}人) ---`);
    for (const r of list.sort((a, b) => b.count - a.count)) {
      const c = r.constraints !== '制約なし' ? `  <- ${r.constraints}` : '';
      console.log(`  ${r.name.padEnd(10)} ${String(r.count).padStart(2)}回  (w=${r.weight})${c}`);
    }
    const counts = list.map(r => r.count);
    const a = counts.reduce((s, c) => s + c, 0) / counts.length;
    console.log(`  平均: ${a.toFixed(1)}回  最大差: ${Math.max(...counts) - Math.min(...counts)}回`);
  };

  printGroup('多め (w>=1.5)', groups.high);
  printGroup('通常 (w=1)', groups.normal);
  printGroup('少なめ (w<=0.5)', groups.low);
  printGroup('免除/途中離脱', groups.exempt);

  console.log('\n--- 全体統計（免除除く） ---');
  console.log(`  人数: ${activeResult.length}人`);
  console.log(`  全員平均: ${avg.toFixed(1)}回`);
  console.log(`  最大: ${max}回 / 最小: ${min}回 / 差: ${max - min}回`);
  console.log(`  標準偏差: ${stdDev.toFixed(2)}`);

  // 同じweight内での偏差チェック
  for (const [label, list] of [['多め', groups.high], ['通常', groups.normal], ['少なめ', groups.low]]) {
    if (list.length < 2) continue;
    const counts = list.map(r => r.count);
    const diff = Math.max(...counts) - Math.min(...counts);
    const sd = Math.sqrt(counts.reduce((sum, c) => sum + (c - counts.reduce((a, b) => a + b, 0) / counts.length) ** 2, 0) / counts.length);
    console.log(`  ${label}グループ内偏差: 最大差${diff}回, SD=${sd.toFixed(2)}`);
  }
}

runTest().catch((err) => {
  console.error('テスト失敗:', err.message);
  process.exit(1);
});
