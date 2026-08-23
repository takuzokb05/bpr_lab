# Claude Code v2.1.238~v2.1.239 大型アップデート：98変更の詳細解析

- URL: https://dev.classmethod.jp/en/articles/20260822-cc-updates-v2-1-239/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-23

## 要約

DevelopersIO（クラスメソッド）によるClaude Code v2.1.238〜v2.1.239の詳細技術解析。2バージョン合計で98件の変更（修正59・改善20・新機能8・セキュリティ8・パフォーマンス2・Breaking Change 1）を網羅。主要新機能：`"keybindingFlavor": "readline"` 設定でBashスタイルショートカット有効化（Ctrl+Wで前の単語削除等）、Cross-Session MessagingがWindowsに拡張（macOS/Linux既存機能と同等）、プラグインマーケットプレイスにdynamic HTTPヘッダー生成機能追加。重要修正：Remote Control切断後の自動再接続、Bedrockプロキシ経由の二重課金バグ修正（サイレント二重請求を防止）。セキュリティ：マスク入力フィールドのクリップボード漏洩防止、フルスクリーンモードでの誤許可防止。keybindingFlavor設定とBedrock二重課金修正が実用上最も重要。
