/**
 * IndexedDB Storage
 * Dexie.jsを使用した画像とセッションの永続化
 */

// Dexieインスタンスの作成
const db = new Dexie('KindleScreenshotDB');

// スキーマ定義
// バージョンを2に上げてインデックス追加を確実に反映
db.version(2).stores({
    screenshots: '++id, sessionId, pageNumber, [sessionId+pageNumber], timestamp',
    sessions: '++id, bookTitle, totalPages, currentPage, status, createdAt, captureArea'
});

/**
 * 新しいセッションを作成
 * @param {string} bookTitle - 書籍タイトル
 * @param {Object} captureArea - 撮影範囲 {x, y, width, height}
 * @returns {Promise<number>} セッションID
 */
async function createSession(bookTitle, captureArea) {
    const sessionId = await db.sessions.add({
        bookTitle: bookTitle || '不明な書籍',
        totalPages: null,
        currentPage: 0,
        status: 'in_progress',
        createdAt: new Date().toISOString(),
        captureArea: captureArea
    });

    console.log(`[DB] セッション作成: ID=${sessionId}`);
    return sessionId;
}

/**
 * セッション情報を更新
 * @param {number} sessionId
 * @param {Object} updates - 更新内容
 */
async function updateSession(sessionId, updates) {
    await db.sessions.update(sessionId, updates);
    console.log(`[DB] セッション更新: ID=${sessionId}`, updates);
}

/**
 * スクリーンショットを保存
 * @param {number} sessionId
 * @param {number} pageNumber
 * @param {string} imageData - Base64画像データ
 */
async function saveScreenshot(sessionId, pageNumber, imageData) {
    await db.screenshots.add({
        sessionId: sessionId,
        pageNumber: pageNumber,
        imageData: imageData,
        timestamp: new Date().toISOString()
    });

    console.log(`[DB] スクリーンショット保存: セッション=${sessionId}, ページ=${pageNumber}`);
}

/**
 * セッションの全スクリーンショットを取得
 * 注意: 大量の画像データをメモリに読み込むため、用途に注意
 * @param {number} sessionId
 * @returns {Promise<Array>} ページ番号順のスクリーンショット配列
 */
async function getScreenshots(sessionId) {
    console.log(`[DB] スクリーンショット全取得開始: セッション=${sessionId}`);
    const screenshots = await db.screenshots
        .where('sessionId')
        .equals(sessionId)
        .sortBy('pageNumber');

    console.log(`[DB] スクリーンショット取得完了: ${screenshots.length}枚`);
    return screenshots;
}

/**
 * 撮影済みのページ番号一覧のみを取得（メモリ節約用）
 * 画像データを読み込まないため非常に高速
 * @param {number} sessionId
 * @returns {Promise<Set<number>>}
 */
async function getCapturedPageNumbers(sessionId) {
    try {
        // [sessionId+pageNumber] インデックスのキーだけを取得（高速・省メモリ）
        const keys = await db.screenshots
            .where('[sessionId+pageNumber]')
            .between([sessionId, Dexie.minKey], [sessionId, Dexie.maxKey])
            .keys();

        // keys は [[sessionId, pageNumber], ...] の形式
        const pageNumbers = keys.map(k => k[1]);
        console.log(`[DB] 撮影済みページ番号取得: ${pageNumbers.length}件`);
        return new Set(pageNumbers);
    } catch (e) {
        console.warn('[DB] インデックス経由の取得に失敗しました。フォールバックします。', e);
        // フォールバック: 全読み込み（メモリ消費大）
        const results = await db.screenshots
            .where('sessionId')
            .equals(sessionId)
            .toArray();
        return new Set(results.map(s => s.pageNumber));
    }
}

/**
 * 画像データを除いたメタデータのみを取得
 * @param {number} sessionId
 */
async function getScreenshotMetadata(sessionId) {
    const results = await db.screenshots
        .where('sessionId')
        .equals(sessionId)
        .toArray();

    return results.map(s => {
        const { imageData, ...metadata } = s;
        return metadata;
    });
}

/**
 * 未完了のセッションを取得
 * @returns {Promise<Object|null>}
 */
async function getIncompleteSession() {
    const sessions = await db.sessions
        .where('status')
        .equals('in_progress')
        .reverse()
        .sortBy('createdAt');

    return sessions.length > 0 ? sessions[0] : null;
}

/**
 * セッションを完了としてマーク
 * @param {number} sessionId
 */
async function completeSession(sessionId) {
    await db.sessions.update(sessionId, {
        status: 'completed',
        completedAt: new Date().toISOString()
    });

    console.log(`[DB] セッション完了: ID=${sessionId}`);
}

/**
 * セッションとそのスクリーンショットを削除
 * @param {number} sessionId
 */
async function deleteSession(sessionId) {
    // スクリーンショットを削除
    await db.screenshots.where('sessionId').equals(sessionId).delete();

    // セッションを削除
    await db.sessions.delete(sessionId);

    console.log(`[DB] セッション削除: ID=${sessionId}`);
}

/**
 * 特定ページのスクリーンショットが存在するか確認
 * @param {number} sessionId
 * @param {number} pageNumber
 * @returns {Promise<boolean>}
 */
async function hasScreenshot(sessionId, pageNumber) {
    const count = await db.screenshots
        .where('[sessionId+pageNumber]')
        .equals([sessionId, pageNumber])
        .count();

    return count > 0;
}

/**
 * セッションの進捗情報を取得
 * @param {number} sessionId
 * @returns {Promise<{total: number, captured: number, percent: number}>}
 */
async function getProgress(sessionId) {
    const session = await db.sessions.get(sessionId);
    const capturedCount = await db.screenshots
        .where('sessionId')
        .equals(sessionId)
        .count();

    const total = session?.totalPages || 0;
    const percent = total > 0 ? Math.round((capturedCount / total) * 100) : 0;

    return {
        total: total,
        captured: capturedCount,
        percent: percent
    };
}

/**
 * データベースをクリア（開発用・トラブル用）
 */
async function clearDatabase() {
    await db.screenshots.clear();
    await db.sessions.clear();
    console.log('[DB] データベースをクリアしました');
}

/**
 * データベースを完全に削除（キャッシュトラブル用）
 */
async function deleteEverything() {
    await db.delete();
    console.log('[DB] データベースを物理的に削除しました。再読み込みで再作成されます。');
    location.reload();
}

// グローバルに公開
window.DB = {
    db,
    createSession,
    updateSession,
    saveScreenshot,
    getScreenshots,
    getCapturedPageNumbers,
    getScreenshotMetadata,
    getIncompleteSession,
    completeSession,
    deleteSession,
    hasScreenshot,
    getProgress,
    clearDatabase,
    deleteEverything
};
