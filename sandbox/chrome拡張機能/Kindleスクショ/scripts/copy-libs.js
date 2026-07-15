/**
 * ライブラリファイルをコピーするスクリプト
 */

const fs = require('fs');
const path = require('path');

const libs = [
    {
        from: 'node_modules/dexie/dist/dexie.min.js',
        to: 'lib/dexie.min.js'
    },
    {
        from: 'node_modules/canvas-confetti/dist/confetti.browser.js',
        to: 'lib/canvas-confetti.min.js'
    },
    {
        from: 'node_modules/jspdf/dist/jspdf.umd.min.js',
        to: 'lib/jspdf.min.js'
    }
];

// libディレクトリ作成
if (!fs.existsSync('lib')) {
    fs.mkdirSync('lib');
}

// ファイルコピー
libs.forEach(lib => {
    const fromPath = path.join(__dirname, '..', lib.from);
    const toPath = path.join(__dirname, '..', lib.to);

    if (fs.existsSync(fromPath)) {
        fs.copyFileSync(fromPath, toPath);
        console.log(`✓ ${lib.from} → ${lib.to}`);
    } else {
        console.error(`✗ ${lib.from} が見つかりません`);
    }
});

console.log('\nライブラリのコピーが完了しました！');
