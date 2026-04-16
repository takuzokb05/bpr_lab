# Claude Agent SDK Deep Dive: What It Means to Use Claude Code as a Library

- URL: https://jidonglab.com/blog/claude-agent-sdk-deep-dive-en/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-04-09

## 要約
Jidong Lab によるClaude Agent SDK（旧Claude Code SDK）の詳細解説記事。旧SDKからの名前変更を踏まえ、「Claude Codeをライブラリとして使う」コンセプトを説明。SDK の3大優位点：①ファイル読み書き・コマンド実行などの組み込みツール（ボイラープレート不要）、②MCPサーバーとの深い統合（Playwright・Slack・GitHubなど）、③18のフックイベントによるエージェント実行への介入機能。Python・TypeScript両SDKでの実装例を提示し、セッション管理（`--resume`フラグ）、権限モード設定（bypassPermissions/acceptEdits等）の使い方を説明。`context-1m-2025-08-07`ベータの2026年4月30日廃止と、Claude Sonnet/Opus 4.6への1Mコンテキスト標準移行も解説。
