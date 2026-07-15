/**
 * UI Overlay
 * 進捗表示、範囲選択、完了アニメーション
 */

const UIOverlay = {
    // 状態
    rangeSelector: null,
    progressOverlay: null,
    completeModal: null,

    /**
     * 範囲選択UIを表示
     * @returns {Promise<{x, y, width, height}>}
     */
    showRangeSelector() {
        return new Promise((resolve) => {
            // オーバーレイ作成
            const overlay = document.createElement('div');
            overlay.id = 'kindle-screenshot-range-selector';

            // ヘルプテキスト
            const help = document.createElement('div');
            help.id = 'kindle-screenshot-range-help';
            help.textContent = 'ドラッグして撮影範囲を指定してください\nKindleのページ表示エリアを選択';
            overlay.appendChild(help);

            // 選択ボックス
            const selectionBox = document.createElement('div');
            selectionBox.id = 'kindle-screenshot-selection-box';
            selectionBox.style.display = 'none';
            overlay.appendChild(selectionBox);

            document.body.appendChild(overlay);
            this.rangeSelector = overlay;

            let startX, startY, isDrawing = false;

            // マウスダウン
            overlay.addEventListener('mousedown', (e) => {
                isDrawing = true;
                startX = e.clientX;
                startY = e.clientY;

                selectionBox.style.left = startX + 'px';
                selectionBox.style.top = startY + 'px';
                selectionBox.style.width = '0px';
                selectionBox.style.height = '0px';
                selectionBox.style.display = 'block';

                help.style.display = 'none';
            });

            // マウス移動
            overlay.addEventListener('mousemove', (e) => {
                if (!isDrawing) return;

                const currentX = e.clientX;
                const currentY = e.clientY;

                const x = Math.min(startX, currentX);
                const y = Math.min(startY, currentY);
                const width = Math.abs(currentX - startX);
                const height = Math.abs(currentY - startY);

                selectionBox.style.left = x + 'px';
                selectionBox.style.top = y + 'px';
                selectionBox.style.width = width + 'px';
                selectionBox.style.height = height + 'px';
            });

            // マウスアップ
            overlay.addEventListener('mouseup', (e) => {
                if (!isDrawing) return;

                const currentX = e.clientX;
                const currentY = e.clientY;

                const width = Math.abs(currentX - startX);
                const height = Math.abs(currentY - startY);
                const x = Math.min(startX, currentX);
                const y = Math.min(startY, currentY);

                console.log('[UIOverlay] mouseup:', { x, y, width, height });

                // 最小サイズチェック（50 -> 10pxに緩和し、ログを出す）
                if (width < 10 || height < 10) {
                    console.warn('[UIOverlay] 選択範囲が小さすぎます:', { width, height });
                    alert(`範囲が小さすぎます（幅:${Math.round(width)}px, 高:${Math.round(height)}px）。\nもう少し大きくドラッグしてください。`);
                    selectionBox.style.display = 'none';
                    help.style.display = 'block';
                    isDrawing = false;
                    return;
                }

                // 範囲を返す
                resolve({ x, y, width, height });
            });
        });
    },

    /**
     * 選択範囲の確認ダイアログを表示
     * @param {string} imageData - テスト撮影したBase64画像
     * @param {string} defaultDirection - 推測される綴じ方向 ('ltr' or 'rtl')
     * @returns {Promise<{confirmed: boolean, direction: string}>}
     */
    showConfirmArea(imageData, defaultDirection = 'ltr') {
        const isRtlDefault = defaultDirection === 'rtl';
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.id = 'kindle-screenshot-confirm-modal';
            modal.innerHTML = `
                <div id="kindle-screenshot-confirm-content">
                  <div id="kindle-screenshot-confirm-title">📸 撮影範囲と進行方向の確認</div>
                  <div id="kindle-screenshot-confirm-message">
                    文字が切れていないか確認し、本の進行方向を選んでください。
                  </div>
                  <div id="kindle-screenshot-confirm-preview-container">
                    <img src="${imageData}" id="kindle-screenshot-confirm-preview">
                  </div>
                  
                  <div id="kindle-screenshot-direction-selector">
                    <p>📖 本の綴じ方向（次ページに進む方向）:</p>
                    <div class="kindle-screenshot-direction-options">
                      <label class="kindle-screenshot-direction-label">
                        <input type="radio" name="page-direction" value="ltr" ${!isRtlDefault ? 'checked' : ''}>
                        <span>👉 <b>左開き</b>（次が右）<br><small>ビジネス書・洋書など</small></span>
                      </label>
                      <label class="kindle-screenshot-direction-label">
                        <input type="radio" name="page-direction" value="rtl" ${isRtlDefault ? 'checked' : ''}>
                        <span>👈 <b>右開き</b>（次が左）<br><small>漫画・縦書き小説など</small></span>
                      </label>
                    </div>
                  </div>

                  <div id="kindle-screenshot-confirm-controls">
                    <button id="kindle-screenshot-confirm-btn-ok">✅ この設定で開始</button>
                    <button id="kindle-screenshot-confirm-btn-retry">🔄 範囲を選び直す</button>
                  </div>
                </div>
            `;

            document.body.appendChild(modal);

            modal.querySelector('#kindle-screenshot-confirm-btn-ok').addEventListener('click', () => {
                const direction = modal.querySelector('input[name="page-direction"]:checked').value;
                modal.remove();
                resolve({ confirmed: true, direction });
            });

            modal.querySelector('#kindle-screenshot-confirm-btn-retry').addEventListener('click', () => {
                modal.remove();
                resolve({ confirmed: false });
            });
        });
    },

    /**
     * 進捗オーバーレイを表示
     * @param {number} current - 現在のページ
     * @param {number} total - 総ページ数
     */
    showProgress(current, total) {
        if (!this.progressOverlay) {
            const overlay = document.createElement('div');
            overlay.id = 'kindle-screenshot-progress';
            overlay.innerHTML = `
                <div id="kindle-screenshot-progress-title">
                  📸 撮影中...
                </div>
                <div id="kindle-screenshot-progress-text">0 / 0</div>
                <div id="kindle-screenshot-progress-bar-container">
                  <div id="kindle-screenshot-progress-bar" style="width: 0%"></div>
                </div>
                <div id="kindle-screenshot-progress-controls">
                  <button class="kindle-screenshot-btn kindle-screenshot-btn-pause">⏸ 一時停止</button>
                  <button class="kindle-screenshot-btn kindle-screenshot-btn-cancel">✕ キャンセル</button>
                </div>
                <div id="kindle-screenshot-thumbnails"></div>
            `;

            document.body.appendChild(overlay);
            this.progressOverlay = overlay;

            // イベントリスナー
            overlay.querySelector('.kindle-screenshot-btn-pause').addEventListener('click', () => {
                window.dispatchEvent(new CustomEvent('kindle-screenshot-pause'));
                const btn = overlay.querySelector('.kindle-screenshot-btn-pause');
                btn.textContent = btn.textContent.includes('一時停止') ? '▶ 再開' : '⏸ 一時停止';
            });

            overlay.querySelector('.kindle-screenshot-btn-cancel').addEventListener('click', () => {
                if (confirm('撮影をキャンセルしますか？\n撮影済みのデータは保持されます。')) {
                    window.dispatchEvent(new CustomEvent('kindle-screenshot-cancel'));
                }
            });
        }

        // 表示を確実にする
        this.progressOverlay.style.visibility = 'visible';
        this.progressOverlay.style.opacity = '1';

        // 進捗更新
        const percent = total > 0 ? Math.round((current / total) * 100) : 0;
        this.progressOverlay.querySelector('#kindle-screenshot-progress-text').textContent = `${current} / ${total}`;
        this.progressOverlay.querySelector('#kindle-screenshot-progress-bar').style.width = `${percent}%`;
    },

    /**
     * サムネイルを追加
     * @param {string} imageData - Base64画像データ
     */
    addThumbnail(imageData) {
        if (!this.progressOverlay) return;

        const container = this.progressOverlay.querySelector('#kindle-screenshot-thumbnails');
        const thumbnail = document.createElement('div');
        thumbnail.className = 'kindle-screenshot-thumbnail';
        thumbnail.style.backgroundImage = `url(${imageData})`;

        container.insertBefore(thumbnail, container.firstChild);

        // 最大10個まで
        while (container.children.length > 10) {
            container.removeChild(container.lastChild);
        }
    },

    /**
     * 進捗オーバーレイを非表示
     */
    hideProgress() {
        if (this.progressOverlay) {
            // removeせずに隠すだけ（撮影に映らないように）
            this.progressOverlay.style.visibility = 'hidden';
            this.progressOverlay.style.opacity = '0';
        }
    },

    /**
     * 完了モーダルを表示
     * @param {number} pageCount - 撮影ページ数
     * @param {Function} onDownload - ダウンロードボタンのコールバック
     */
    async showCompletion(pageCount, onDownload) {
        // 紙吹雪アニメーション
        if (window.confetti) {
            const duration = 3000;
            const end = Date.now() + duration;

            const frame = () => {
                confetti({
                    particleCount: 3,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0 },
                    colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c']
                });
                confetti({
                    particleCount: 3,
                    angle: 120,
                    spread: 55,
                    origin: { x: 1 },
                    colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c']
                });

                if (Date.now() < end) {
                    requestAnimationFrame(frame);
                }
            };

            frame();
        }

        // モーダル作成
        const modal = document.createElement('div');
        modal.id = 'kindle-screenshot-complete-modal';
        modal.innerHTML = `
      <div id="kindle-screenshot-complete-content">
        <div id="kindle-screenshot-complete-title">
          🎉 撮影完了！
        </div>
        <div id="kindle-screenshot-complete-message">
          ${pageCount}ページのPDF化が完了しました！<br>
          お疲れ様でした 🎊
        </div>
        <button id="kindle-screenshot-complete-download-btn">
          📥 PDFをダウンロード
        </button>
      </div>
    `;

        document.body.appendChild(modal);
        this.completeModal = modal;

        // ダウンロードボタン
        modal.querySelector('#kindle-screenshot-complete-download-btn').addEventListener('click', async () => {
            await onDownload();
            modal.remove();
            this.completeModal = null;
        });
    },

    /**
     * すべてのUIを非表示
     */
    hideAll() {
        if (this.rangeSelector) {
            this.rangeSelector.remove();
            this.rangeSelector = null;
        }
        if (this.progressOverlay) {
            this.progressOverlay.remove();
            this.progressOverlay = null;
        }
        if (this.completeModal) {
            this.completeModal.remove();
            this.completeModal = null;
        }
    },

    /**
     * 撮影のためにUIを一時的に隠す
     */
    hideForCapture() {
        const elements = [
            this.progressOverlay,
            document.getElementById('kindle-screenshot-start-btn'),
            document.getElementById('kindle-screenshot-range-selector')
        ];

        elements.forEach(el => {
            if (el) {
                el.style.opacity = '0';
                el.style.pointerEvents = 'none';
            }
        });
    },

    /**
     * 撮影後にUIを再表示する
     */
    showAfterCapture() {
        const elements = [
            this.progressOverlay,
            document.getElementById('kindle-screenshot-start-btn')
        ];

        elements.forEach(el => {
            if (el) {
                el.style.opacity = '1';
                el.style.pointerEvents = 'auto';
            }
        });
    }
};

// グローバルに公開
window.UIOverlay = UIOverlay;
