# How to Use the Claude Agent SDK: 11 Steps, 90 Min [2026]

- URL: https://tech-insider.org/au/how-to-use-claude-agent-sdk-2026/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-30

## 投稿内容

The Claude Agent SDK is a free open-source SDK provided by Anthropic that allows calling Claude Code's core engine as a library, enabling autonomous AI agents with capabilities like file read/write, Bash execution, web search, and subagent launch through just a few lines of Python code. This guide walks through 11 steps to build your first agent in approximately 90 minutes.

## 要約

Claude Agent SDKの11ステップ完全入門ガイド（Tech Insider、2026年）。約90分でPythonエージェントを構築：
- **基本構造**: @toolデコレータで任意のPython関数をClaudeが呼べるツールに変換、query()関数でエージェントループ実行
- **組み込みツール群**: ファイルR/W・Bash実行・WebSearch・サブエージェント並列起動がゼロ設定で利用可能
- **実装例（リポジトリトリアージエージェント）**: ①TODO/FIXME/HACKコメント + コードスメルをスキャン ②各発見をサブエージェントに委譲して重大度評価 ③Markdownレポートに集約出力
- **MCPとの組み合わせ**: GitHub公式MCPサーバー連携でPR作成・Issue検索を自然言語操作
- **特徴**: Anthropicが無償公開するOSSで数行のPythonから始められる。内部でClaude Codeのコアエンジンを呼び出すためフル機能アクセス可能
- **2026年時点の位置付け**: Claude Code CLIの機能をライブラリとして利用したい開発者・CI/CDパイプライン組み込み用途に最適
