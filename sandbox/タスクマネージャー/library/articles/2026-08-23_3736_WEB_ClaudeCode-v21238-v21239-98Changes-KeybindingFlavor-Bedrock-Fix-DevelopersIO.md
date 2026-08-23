# Claude Code v2.1.238~v2.1.239：98変更の技術詳解（DevelopersIO）

- URL: https://dev.classmethod.jp/en/articles/20260822-cc-updates-v2-1-239/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-23

## 投稿内容

DevelopersIO（クラスメソッド）によるClaude Code v2.1.238〜v2.1.239の2バージョン合計98変更の詳細技術解析記事（2026-08-22公開）。

## 要約

98変更の内訳：修正59件・改善20件・新機能8件・セキュリティ8件・パフォーマンス2件・Breaking Change 1件。フォーカスはRemote Control信頼性・フルスクリーンモード・プラグインマーケットプレイス。

**主要新機能（8件）：**
1. `keybindingFlavor: "readline"` 設定 → Bashスタイルキーボードショートカット有効化（Ctrl+Wで前単語削除等）
2. Cross-Session MessagingがWindowsに拡張（macOS/Linux既存機能と同等）
3. プラグインマーケットプレイスに`headersHelper`追加（動的HTTPヘッダー生成、ユーザー確認フロー付き）
4. Bedrock・Vertex・Foundry等で全画面レンダラーオファーを表示（従来除外環境に追加）
5. `/claude-api upgrade`コマンド（Python 0.x→1.x移行半自動化）
6. Cloud sessionsのプラグイン同期改善（claude.aiから同期されたプラグインが`name@synced`として表示）
7. Alpine/muslビルドで画像貼り付け・クリップボード・音声キャプチャアドオンがロード可能に

**重要修正（59件中主要）：**
- Bedrock経由の**二重課金バグ修正**（Content-Typeヘッダーを除去するプロキシ使用時のサイレント二重請求を防止）
- Remote Control切断後の自動再接続（短時間の通信断でも継続）
- モバイルからのモデル選択がターミナルに正しく反映

**セキュリティ（8件）：**
- マスク入力フィールドのクリップボード経由漏洩を防止
- フルスクリーンモードでフォーカスクリックによる誤許可プロンプト発火を防止
- 拒否されたポリシーリクエストがサイレント再送されるバグを修正
