# Claude Code vs Claude Agent SDK: Which Is for What

- URL: https://www.augmentcode.com/tools/claude-code-vs-claude-agent-sdk
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-08

## 投稿内容

Augment Code による Claude Code と Claude Agent SDK の明確な使い分けガイド。

## 要約

Claude Code は開発者がターミナルで使うインタラクティブな CLI ツール（エディタ統合・ファイル編集・コマンド実行）。Claude Agent SDK は Claude Code の内部エンジン（ツール・エージェントループ・コンテキスト管理）をプログラムから制御するライブラリ。重要な事実：Claude Code 自体が Agent SDK を使って構築されており、同一の tool-use-first アーキテクチャを共有する。ユースケース分類：CI/CDパイプライン・自動コードレビュー・バッチ処理・カスタムエージェント構築 → Agent SDK、日々の開発タスク・リファクタリング・デバッグ・インタラクティブ作業 → Claude Code。Agent SDK は Python/TypeScript で利用可能、カスタムツール定義・マルチエージェント構成・サブエージェント委譲が可能。判断基準：「人間がインタラクティブに使う」→ Claude Code、「コードから自動実行する」→ Agent SDK。
