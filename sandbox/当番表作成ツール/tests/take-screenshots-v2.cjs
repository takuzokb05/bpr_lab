/**
 * 当番表作成ツール V2 — マニュアル用スクリーンショット撮影スクリプト
 *
 * 使い方:
 *   node tests/take-screenshots-v2.cjs
 *
 * 出力先: tests/screenshots/manual/
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const HTML_PATH = path.resolve(__dirname, '../src/当番表作成ツール-v2.html');
const OUTPUT_DIR = path.resolve(__dirname, 'screenshots/manual');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// テスト用データ（マニュアルに映えるよう調整）
const TEST_DATA = {
  calendar: {
    year: 2026,
    month: 4,
    holidays: [29],
    workdayOverrides: [],
    dayTimeSettings: {},
  },
  slots: [
    { id: 'slot-1', name: '窓口当番', startTime: '09:00', endTime: '12:00', requiredCount: 1, applyMode: 'workdays', specificDays: [] },
    { id: 'slot-2', name: '電話当番', startTime: '09:00', endTime: '17:00', requiredCount: 1, applyMode: 'workdays', specificDays: [] },
    { id: 'slot-3', name: '昼当番', startTime: '12:00', endTime: '13:00', requiredCount: 2, applyMode: 'workdays', specificDays: [] },
    { id: 'slot-4', name: '土曜窓口', startTime: '09:00', endTime: '12:00', requiredCount: 1, applyMode: 'specific', specificDays: [11, 25], allowedTags: ['tag-a'] },
  ],
  tags: [
    { id: 'tag-a', name: 'A班', color: '#2563EB' },
    { id: 'tag-b', name: 'B班', color: '#16A34A' },
    { id: 'tag-c', name: '会計年度', color: '#D97706' },
  ],
  staff: [
    { id: 's1', name: '山田太郎', dutyWeight: 1.5, tags: ['tag-a'], shortTime: null, fixedDays: [], dayOffWeekdays: [], unavailableDates: [], trainingPairId: null, exemptFromDate: null },
    { id: 's2', name: '佐藤花子', dutyWeight: 1, tags: ['tag-a'], shortTime: null, fixedDays: [{ slotId: 'slot-1', weekdays: [1, 3] }], dayOffWeekdays: [], unavailableDates: [], trainingPairId: null, exemptFromDate: null },
    { id: 's3', name: '鈴木一郎', dutyWeight: 0.5, tags: ['tag-a'], shortTime: { start: '09:00', end: '13:00' }, fixedDays: [], dayOffWeekdays: [], unavailableDates: [], trainingPairId: null, exemptFromDate: null },
    { id: 's4', name: '田中美咲', dutyWeight: 1, tags: ['tag-b'], shortTime: null, fixedDays: [], dayOffWeekdays: [], unavailableDates: ['2026-04-15'], trainingPairId: null, exemptFromDate: null },
    { id: 's5', name: '高橋健太', dutyWeight: 1, tags: ['tag-b'], shortTime: null, fixedDays: [], dayOffWeekdays: [], unavailableDates: [], trainingPairId: null, exemptFromDate: null },
    { id: 's6', name: '伊藤真理', dutyWeight: 1, tags: ['tag-b'], shortTime: null, fixedDays: [], dayOffWeekdays: [3], unavailableDates: [], trainingPairId: null, exemptFromDate: null },
    { id: 's7', name: '渡辺修', dutyWeight: 1, tags: ['tag-c'], shortTime: null, fixedDays: [], dayOffWeekdays: [3], unavailableDates: [], trainingPairId: null, exemptFromDate: null },
    { id: 's8', name: '中村新人', dutyWeight: 1, tags: ['tag-a'], shortTime: null, fixedDays: [], dayOffWeekdays: [], unavailableDates: [], trainingPairId: 's9', exemptFromDate: null },
    { id: 's9', name: '小林先輩', dutyWeight: 1, tags: ['tag-a'], shortTime: null, fixedDays: [], dayOffWeekdays: [], unavailableDates: [], trainingPairId: 's8', exemptFromDate: null },
    { id: 's10', name: '加藤退職', dutyWeight: 1, tags: ['tag-b'], shortTime: null, fixedDays: [], dayOffWeekdays: [], unavailableDates: [], trainingPairId: null, exemptFromDate: '2026-04-16' },
  ],
  assignments: {},
  neoIds: {},
};

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function clickTab(page, tabLabel) {
  await page.evaluate((label) => {
    const tabs = document.querySelectorAll('#settings-tabs .tab');
    for (const tab of tabs) {
      if (tab.textContent.trim() === label) {
        tab.click();
        return;
      }
    }
  }, tabLabel);
  await wait(400);
}

async function takeScreenshots() {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });

  const fileUrl = `file://${HTML_PATH.replace(/\\/g, '/')}`;

  // === 1. 初期画面 ===
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });
  await page.evaluate(() => localStorage.clear());
  await page.reload({ waitUntil: 'networkidle0' });
  await page.screenshot({ path: path.join(OUTPUT_DIR, '01_initial.png'), fullPage: true });
  console.log('01_initial.png');

  // === テストデータ投入 ===
  await page.evaluate((data) => {
    localStorage.setItem('toban_tool_data', JSON.stringify(data));
  }, TEST_DATA);
  await page.reload({ waitUntil: 'networkidle0' });

  // === 2. カレンダータブ ===
  await clickTab(page, 'カレンダー');
  await page.screenshot({ path: path.join(OUTPUT_DIR, '02_calendar.png'), fullPage: false });
  console.log('02_calendar.png');

  // === 3. 当番枠タブ ===
  await clickTab(page, '当番枠');
  await page.screenshot({ path: path.join(OUTPUT_DIR, '03_slots.png'), fullPage: false });
  console.log('03_slots.png');

  // === 4. タグタブ ===
  await clickTab(page, 'タグ');
  await page.screenshot({ path: path.join(OUTPUT_DIR, '04_tags.png'), fullPage: false });
  console.log('04_tags.png');

  // === 5. 職員タブ ===
  await clickTab(page, '職員');
  await page.screenshot({ path: path.join(OUTPUT_DIR, '05_staff.png'), fullPage: false });
  console.log('05_staff.png');

  // === 6. NEO連携タブ ===
  await clickTab(page, 'NEO連携');
  await page.screenshot({ path: path.join(OUTPUT_DIR, '06_neo.png'), fullPage: false });
  console.log('06_neo.png');

  // === 7. 自動割り当て実行後 ===
  // 設定パネルを閉じる
  const toggle = await page.$('#settings-toggle');
  if (toggle) {
    await toggle.click();
    await wait(300);
  }

  // 自動割り当てボタンをクリック
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('.btn-success');
    for (const btn of buttons) {
      if (btn.textContent.includes('自動割り当て')) {
        btn.click();
        return;
      }
    }
  });
  await wait(800);

  // 割り当て結果モーダル（条件列付き）のスクショを撮影
  await page.screenshot({ path: path.join(OUTPUT_DIR, '07a_stats_modal.png'), fullPage: false });
  console.log('07a_stats_modal.png');

  // モーダルを閉じる
  await page.evaluate(() => {
    const closeBtn = document.querySelector('.modal-close');
    if (closeBtn) closeBtn.click();
    const buttons = document.querySelectorAll('.modal .btn');
    for (const btn of buttons) {
      if (btn.textContent.includes('閉じる')) {
        btn.click();
        return;
      }
    }
  });
  await wait(400);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '07_schedule.png'), fullPage: true });
  console.log('07_schedule.png');

  // === 7b. 「当番回数を確認」ボタンで統計モーダルを開く ===
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('.btn-outline');
    for (const btn of buttons) {
      if (btn.textContent.includes('当番回数を確認')) {
        btn.click();
        return;
      }
    }
  });
  await wait(600);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '07b_count_check.png'), fullPage: false });
  console.log('07b_count_check.png');

  // モーダルを閉じる
  await page.evaluate(() => {
    const closeBtn = document.querySelector('.modal-close');
    if (closeBtn) closeBtn.click();
  });
  await wait(300);

  // === 8. 出力ボタンエリア（フッター付近） ===
  // スクロールしてExcelコピー・印刷・NEOボタンを表示
  await page.evaluate(() => {
    const outputEl = document.getElementById('output-section');
    if (outputEl) outputEl.scrollIntoView({ behavior: 'instant', block: 'center' });
  });
  await wait(300);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '08_output.png'), fullPage: false });
  console.log('08_output.png');

  // === 9. 印刷プレビュー ===
  await page.emulateMediaType('print');
  await page.screenshot({ path: path.join(OUTPUT_DIR, '09_print.png'), fullPage: true });
  console.log('09_print.png');

  await browser.close();
  console.log(`\n全スクリーンショットを ${OUTPUT_DIR} に保存しました`);
}

takeScreenshots().catch((err) => {
  console.error('撮影失敗:', err.message);
  process.exit(1);
});
