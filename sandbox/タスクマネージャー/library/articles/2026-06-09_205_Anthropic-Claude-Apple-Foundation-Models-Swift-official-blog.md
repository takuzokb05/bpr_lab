# Claude support for Apple Foundation Models framework — Anthropic公式ブログ

- URL: https://claude.com/blog/claude-for-foundation-models
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-09

## 投稿内容
Anthropic公式ブログによるClaude × Apple Foundation Modelsフレームワーク統合発表。

技術詳細：AppleのFoundation Models frameworkを介してClaudeを呼び出す新しいSwiftパッケージをリリース。iOS 27/iPadOS 27/macOS 27/visionOS 27/watchOS 27対応。Appleの新しいLanguageModelプロトコルを実装。

主な機能：on-deviceモデルからClaudeへの移行がSwift Package Manager更新のみで可能。Claudeは複雑なワークフロー、コード生成、Webサーチ、データ分析コード実行をサポート。ガイデッド生成により型付きSwift値を3行のコードで返す。

使用パターン：開発チームはオンデバイスモデルでプロトタイプを作成し、複雑なクエリが発生した際にClaudeへ自動ルーティング。スワップ時はSPM依存関係の更新のみ（セッションロジック変更不要）。

## 要約
Anthropic公式によるApple Foundation Models統合の一次情報。SwiftパッケージでiOS/macOS 27系全プラットフォーム対応。LanguageModelプロトコル実装で他クラウドプロバイダー（Google Gemini等）と同一APIサーフェスを共有。on-device → Claudeのハイブリッドアーキテクチャが容易に実現でき、iOSアプリへのClaude統合の標準パスとなる重要な公式ドキュメント。
