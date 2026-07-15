/**
 * 当番表作成ツール V2 — HTMLマニュアル生成スクリプト
 *
 * スクショをBase64エンコードして単一HTMLマニュアルを生成する。
 *
 * 使い方:
 *   node tests/take-screenshots-v2.cjs   （先にスクショ撮影）
 *   node tests/generate-manual.cjs       （マニュアル生成）
 *
 * 出力: docs/manual.html
 */

const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.resolve(__dirname, 'screenshots/manual');
const OUTPUT_PATH = path.resolve(__dirname, '../docs/manual.html');

// スクショをBase64で読み込む
function loadImage(filename) {
  const filepath = path.join(SCREENSHOT_DIR, filename);
  if (!fs.existsSync(filepath)) {
    console.warn(`画像が見つかりません: ${filename}`);
    return '';
  }
  const buf = fs.readFileSync(filepath);
  return `data:image/png;base64,${buf.toString('base64')}`;
}

// マニュアルの章構成
const chapters = [
  {
    id: 'overview',
    title: 'はじめに',
    image: null,
    content: `
      <p>「当番表作成ツール」は、職員の制約条件（時短勤務・公休・固定曜日・ペア研修など）を考慮して、
      当番表を自動的に作成するツールです。</p>
      <h3>特長</h3>
      <ul>
        <li>ブラウザだけで動作（インストール不要・インターネット接続不要）</li>
        <li>職員の個別制約を登録するだけで、公平な割り当てを自動計算</li>
        <li>Excelへのコピー、印刷、デスクネッツNEO連携に対応</li>
        <li>データはブラウザ内に保存（サーバーへの送信なし）</li>
      </ul>
      <h3>動作環境</h3>
      <ul>
        <li>Google Chrome または Microsoft Edge（最新版推奨）</li>
        <li>画面解像度: 1280x900 以上を推奨</li>
      </ul>
      <h3>基本的な流れ</h3>
      <ol>
        <li><strong>カレンダー設定</strong> — 対象月と祝日を設定</li>
        <li><strong>当番枠の設定</strong> — 当番の種類・時間・必要人数を登録</li>
        <li><strong>タグの作成</strong> — 職員を分類するタグを作成（任意）</li>
        <li><strong>職員の登録</strong> — 職員情報と個別制約を登録</li>
        <li><strong>自動割り当て</strong> — ボタン1つで当番表を自動生成</li>
        <li><strong>出力</strong> — Excel / 印刷 / CSV で結果を取り出し</li>
      </ol>`,
  },
  {
    id: 'initial',
    title: '画面の全体構成',
    image: '01_initial.png',
    content: `
      <p>ツールを開くと、上記の画面が表示されます。画面は大きく3つのエリアに分かれています。</p>
      <table class="desc-table">
        <tr><th>エリア</th><th>説明</th></tr>
        <tr><td>設定パネル（上部）</td><td>カレンダー・当番枠・タグ・職員・NEO連携の5つのタブで構成。「設定」をクリックすると開閉できます</td></tr>
        <tr><td>当番表グリッド（中央）</td><td>月間の当番表が表示されます。自動割り当て後にここに名前が入ります</td></tr>
        <tr><td>出力エリア（下部）</td><td>Excelコピー・印刷・NEO用CSV・JSONバックアップなどのボタンが並びます</td></tr>
      </table>`,
  },
  {
    id: 'calendar',
    title: 'Step 1: カレンダー設定',
    image: '02_calendar.png',
    content: `
      <p>「カレンダー」タブで対象月と祝日を設定します。</p>
      <h3>操作手順</h3>
      <ol>
        <li>「対象年月」のプルダウンから、当番表を作りたい年月を選びます</li>
        <li>ミニカレンダーの日付をクリックして、祝日を設定します
          <ul>
            <li>クリックすると<span class="highlight-red">赤色（祝日）</span>に変わります</li>
            <li>もう一度クリックすると元に戻ります</li>
            <li>土日をクリックすると<span class="highlight-green">緑色（勤務日に変更）</span>にできます</li>
          </ul>
        </li>
      </ol>
      <div class="tip">
        <strong>ポイント:</strong> 祝日に設定した日は、当番表で「祝日」と表示され、自動割り当ての対象外になります。
      </div>`,
  },
  {
    id: 'slots',
    title: 'Step 2: 当番枠の設定',
    image: '03_slots.png',
    content: `
      <p>「当番枠」タブで、どんな種類の当番があるかを登録します。</p>
      <h3>操作手順</h3>
      <ol>
        <li>「+ 枠を追加」ボタンをクリックして、新しい当番枠を作成します</li>
        <li>以下の項目を入力します:
          <ul>
            <li><strong>枠名</strong> — 当番の名前（例: 窓口当番、電話当番、昼当番）</li>
            <li><strong>時間</strong> — 開始時刻と終了時刻</li>
            <li><strong>必要人数</strong> — その枠に必要な人数（例: 昼当番は2人）</li>
          </ul>
        </li>
        <li>不要な枠は右側の「削除」ボタンで削除できます</li>
      </ol>
      <div class="tip">
        <strong>ポイント:</strong> 時短勤務の職員は、勤務時間外の枠には自動的に割り当てられません。
        例えば13時までの時短勤務の職員は、9:00〜17:00の電話当番には割り当てられません。
      </div>`,
  },
  {
    id: 'tags',
    title: 'Step 3: タグの作成',
    image: '04_tags.png',
    content: `
      <p>「タグ」タブで、職員を分類するためのタグを作成します。タグの作成は任意です。</p>
      <h3>操作手順</h3>
      <ol>
        <li>「+ タグを追加」ボタンをクリック</li>
        <li>タグ名を入力（例: A班、B班、会計年度任用）</li>
        <li>色を選択（自動で異なる色が割り当てられます）</li>
      </ol>
      <div class="tip">
        <strong>ポイント:</strong> タグは当番表の見た目を分かりやすくするためのもので、
        自動割り当てのロジックには影響しません。
        職員名の横にタグのバッジが表示されるので、班やグループの識別に便利です。
      </div>`,
  },
  {
    id: 'staff',
    title: 'Step 4: 職員の登録',
    image: '05_staff.png',
    content: `
      <p>「職員」タブで、当番に参加する職員を登録します。ここが最も重要な設定です。</p>
      <h3>操作手順</h3>
      <ol>
        <li>「+ 職員を追加」ボタンをクリック</li>
        <li>職員名を入力</li>
        <li><strong>当番頻度</strong>を選択（多め / 通常 / 少なめ）
          <ul>
            <li>「多め」の職員には約1.5倍、「少なめ」は約0.5倍の回数が割り振られます</li>
          </ul>
        </li>
        <li>該当する制約条件にチェックを入れて詳細を設定:
          <table class="desc-table">
            <tr><th>制約</th><th>説明</th><th>例</th></tr>
            <tr><td>時短勤務</td><td>勤務時間が通常より短い場合</td><td>09:00〜13:00</td></tr>
            <tr><td>曜日固定</td><td>特定の曜日に特定の枠を担当する場合</td><td>窓口当番を月・水に固定</td></tr>
            <tr><td>不可日</td><td>出勤できない曜日・日付を指定<br>（毎週の公休曜日と個別の日付をまとめて設定）</td><td>毎週水曜休み + 4/15出張</td></tr>
            <tr><td>研修ペア</td><td>新人と先輩を同じ日に割り当てたい場合</td><td>中村新人と小林先輩</td></tr>
            <tr><td>対象外開始日</td><td>途中で異動・退職する場合</td><td>4/16から対象外</td></tr>
          </table>
        </li>
        <li>必要に応じてタグを選択</li>
      </ol>
      <p>登録済みの職員はカード形式で一覧表示されます。制約条件はバッジで確認できます。
      「編集」で変更、「削除」で削除できます。</p>
      <div class="tip">
        <strong>ポイント:</strong> 5人以上登録すると検索ボックスが表示されます。名前やタグ名で絞り込めます。
      </div>`,
  },
  {
    id: 'schedule',
    title: 'Step 5: 自動割り当て',
    image: '07_schedule.png',
    content: `
      <p>設定が完了したら、「自動割り当て」ボタンを押すだけで当番表が自動生成されます。</p>
      <h3>割り当てのルール</h3>
      <p>自動割り当ては、以下の優先順位でルールを適用します:</p>
      <ol>
        <li><strong>絶対ルール（必ず守る）</strong>
          <ul>
            <li>公休日・不可日・祝日には割り当てない</li>
            <li>時短勤務の職員は勤務時間外の枠に割り当てない</li>
            <li>対象外開始日以降は割り当てない</li>
          </ul>
        </li>
        <li><strong>同日重複の禁止</strong> — 同じ日に同じ職員を複数の枠に割り当てない</li>
        <li><strong>連続回避</strong> — なるべく連日にならないよう分散</li>
        <li><strong>回数の公平性</strong> — 当番頻度（多め/通常/少なめ）を加味しつつ、なるべく均等になるよう調整</li>
      </ol>
      <h3>手動での修正</h3>
      <p>自動割り当て後に、当番表のセルをクリックすると職員を手動で変更できます。
      「割り当てをクリア」で全てリセットすることもできます。</p>
      <div class="tip">
        <strong>ポイント:</strong> 曜日固定の職員は、指定された曜日に優先的に割り当てられます。
        研修ペアは同じ日の同じ枠に一緒に割り当てられます。
      </div>`,
  },
  {
    id: 'output',
    title: 'Step 6: 出力',
    image: '08_output.png',
    content: `
      <p>完成した当番表は、複数の方法で出力できます。</p>
      <table class="desc-table">
        <tr><th>ボタン</th><th>機能</th><th>使い方</th></tr>
        <tr><td>Excelにコピー</td><td>クリップボードにコピー</td><td>Excelを開いて Ctrl+V で貼り付け</td></tr>
        <tr><td>印刷</td><td>印刷プレビューを表示</td><td>A4用紙に最適化されたレイアウトで印刷</td></tr>
        <tr><td>NEO用CSVダウンロード</td><td>デスクネッツNEO用のCSVを出力</td><td>NEOのスケジュールにインポート可能</td></tr>
        <tr><td>JSONエクスポート</td><td>全データをJSONファイルで保存</td><td>バックアップや他のPCへの移行に使用</td></tr>
        <tr><td>JSONインポート</td><td>JSONファイルからデータを復元</td><td>バックアップからの復元に使用</td></tr>
        <tr><td>元に戻す</td><td>直前の割り当て操作を取り消し</td><td>手動変更を間違えた場合に使用</td></tr>
      </table>
      <div class="tip">
        <strong>ポイント:</strong> データはブラウザ内（localStorage）に保存されます。
        ブラウザの履歴削除や端末入替で消える可能性があるため、
        定期的に「JSONエクスポート」でバックアップすることを推奨します。
      </div>`,
  },
  {
    id: 'print',
    title: '印刷プレビュー',
    image: '09_print.png',
    content: `
      <p>「印刷」ボタンを押すと、印刷用のレイアウトでプレビューが表示されます。</p>
      <ul>
        <li>ヘッダー・設定パネル・ボタン類は非表示になります</li>
        <li>A4縦向きに最適化されています</li>
        <li>ブラウザの印刷ダイアログで用紙サイズやプリンターを選択してください</li>
      </ul>`,
  },
  {
    id: 'faq',
    title: 'よくある質問',
    image: null,
    content: `
      <dl class="faq-list">
        <dt>Q: データはどこに保存されていますか？</dt>
        <dd>A: ブラウザ内（localStorage）に保存されます。サーバーには送信されません。
        ただし、ブラウザの履歴削除や端末入替で消える可能性があるため、
        「JSONエクスポート」で定期的にバックアップしてください。</dd>

        <dt>Q: 別のPCで使いたい場合は？</dt>
        <dd>A: 「JSONエクスポート」でデータを保存し、別のPCで「JSONインポート」してください。
        HTMLファイル自体もコピーが必要です。</dd>

        <dt>Q: 自動割り当ての結果を一部だけ変更したい</dt>
        <dd>A: 当番表のセルをクリックすると、その日・その枠の担当者を手動で選択できます。
        間違えた場合は「元に戻す」ボタンで取り消せます。</dd>

        <dt>Q: 職員が月の途中で異動する場合は？</dt>
        <dd>A: 職員の編集画面で「対象外開始日」を設定してください。
        その日以降は自動割り当ての対象外になります。</dd>

        <dt>Q: デスクネッツNEOに連携するには？</dt>
        <dd>A: 「NEO連携」タブで職員名とNEOのシステムIDを紐づけてから、
        「NEO用CSVダウンロード」でCSVを出力してください。</dd>

        <dt>Q: 画面が崩れる・動かない場合は？</dt>
        <dd>A: Google Chrome または Microsoft Edge の最新版をお使いください。
        Internet Explorer には対応していません。</dd>
      </dl>`,
  },
];

// HTML生成
function generateHTML() {
  // 画像を読み込み
  const images = {};
  for (const ch of chapters) {
    if (ch.image) {
      images[ch.image] = loadImage(ch.image);
    }
  }

  // 目次生成
  const tocItems = chapters.map((ch, i) => {
    const num = ch.id === 'overview' || ch.id === 'faq' ? '' : '';
    return `<li><a href="#${ch.id}">${ch.title}</a></li>`;
  }).join('\n        ');

  // 章生成
  const chapterSections = chapters.map((ch) => {
    const imgTag = ch.image && images[ch.image]
      ? `<div class="screenshot"><img src="${images[ch.image]}" alt="${ch.title}" loading="lazy"></div>`
      : '';
    return `
    <section id="${ch.id}" class="chapter">
      <h2>${ch.title}</h2>
      ${imgTag}
      <div class="chapter-body">
        ${ch.content}
      </div>
    </section>`;
  }).join('\n');

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>当番表作成ツール 操作マニュアル</title>
<style>
/* === 基本 === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Yu Gothic Medium", "Yu Gothic", "Meiryo", sans-serif;
  background: #f5f7fa; color: #1a1a2e; font-size: 15px; line-height: 1.8;
}

/* === ヘッダー === */
.manual-header {
  background: linear-gradient(135deg, #000613, #001F3F);
  color: #fff; padding: 40px 24px; text-align: center;
}
.manual-header h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
.manual-header p { font-size: 14px; opacity: .8; }

/* === ナビゲーション（目次） === */
.toc {
  max-width: 880px; margin: -20px auto 0; padding: 24px 32px;
  background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,.06);
  position: relative; z-index: 1;
}
.toc h2 { font-size: 16px; color: #001F3F; margin-bottom: 12px; }
.toc ol {
  list-style: none; counter-reset: toc-counter;
  display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 4px 24px;
}
.toc li { counter-increment: toc-counter; }
.toc li::before {
  content: counter(toc-counter) "."; color: #001F3F; font-weight: 700;
  display: inline-block; width: 24px; font-size: 13px;
}
.toc a { color: #2563EB; text-decoration: none; font-size: 14px; }
.toc a:hover { text-decoration: underline; }

/* === 本文エリア === */
.manual-body { max-width: 880px; margin: 32px auto; padding: 0 16px; }

/* === 章 === */
.chapter {
  background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.04);
  margin-bottom: 28px; overflow: hidden;
}
.chapter h2 {
  background: #f0f4fa; padding: 18px 28px; font-size: 20px; color: #001F3F;
  border-bottom: 1px solid #e2e6ef;
}
.chapter-body { padding: 24px 28px; }
.chapter-body h3 { font-size: 16px; color: #001F3F; margin: 20px 0 8px; }
.chapter-body p { margin-bottom: 12px; }
.chapter-body ul, .chapter-body ol { margin: 0 0 12px 20px; }
.chapter-body li { margin-bottom: 4px; }
.chapter-body ul ul { margin-top: 4px; }

/* === スクリーンショット === */
.screenshot {
  padding: 16px 28px; background: #fafbfd; border-bottom: 1px solid #e2e6ef;
}
.screenshot img {
  max-width: 100%; height: auto; border-radius: 8px;
  box-shadow: 0 2px 16px rgba(0,0,0,.08); display: block; margin: 0 auto;
}

/* === 説明テーブル === */
.desc-table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }
.desc-table th {
  background: #f0f4fa; padding: 10px 14px; text-align: left; font-weight: 600;
  border-bottom: 2px solid #d0d7e6; color: #001F3F; white-space: nowrap;
}
.desc-table td {
  padding: 10px 14px; border-bottom: 1px solid #e8ecf4; vertical-align: top;
}
.desc-table tr:last-child td { border-bottom: none; }

/* === ヒント === */
.tip {
  background: #EFF6FF; border-left: 4px solid #2563EB; border-radius: 0 8px 8px 0;
  padding: 14px 18px; margin: 16px 0; font-size: 14px; color: #1e3a5f;
}
.tip strong { color: #1d4ed8; }

/* === ハイライト === */
.highlight-red { color: #dc2626; font-weight: 600; }
.highlight-green { color: #16a34a; font-weight: 600; }

/* === FAQ === */
.faq-list dt {
  font-weight: 700; color: #001F3F; margin-top: 20px; padding-bottom: 4px;
  border-bottom: 1px solid #e8ecf4; font-size: 15px;
}
.faq-list dt:first-child { margin-top: 0; }
.faq-list dd { margin: 8px 0 0 0; padding-left: 24px; font-size: 14px; color: #333; }

/* === フッター === */
.manual-footer {
  text-align: center; padding: 24px; font-size: 12px; color: #999;
  border-top: 1px solid #e8ecf4; margin-top: 20px;
}

/* === 印刷 === */
@media print {
  body { background: #fff; font-size: 12px; }
  .manual-header { padding: 20px; background: #001F3F !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .toc, .chapter { box-shadow: none; border: 1px solid #ddd; }
  .screenshot img { max-width: 90%; box-shadow: none; }
  .chapter { break-inside: avoid; }
  @page { size: A4; margin: 15mm; }
}
</style>
</head>
<body>

<header class="manual-header">
  <h1>当番表作成ツール 操作マニュアル</h1>
  <p>職員の制約を考慮した自動割り当て + Excel / 印刷 / デスクネッツNEO連携</p>
</header>

<nav class="toc">
  <h2>目次</h2>
  <ol>
    ${tocItems}
  </ol>
</nav>

<div class="manual-body">
  ${chapterSections}
</div>

<footer class="manual-footer">
  当番表作成ツール 操作マニュアル | 作成日: ${new Date().toLocaleDateString('ja-JP')}
</footer>

</body>
</html>`;
}

// 出力
const html = generateHTML();
fs.writeFileSync(OUTPUT_PATH, html, 'utf8');
console.log(`マニュアルを生成しました: ${OUTPUT_PATH}`);
console.log(`ファイルサイズ: ${(Buffer.byteLength(html) / 1024).toFixed(0)} KB`);
