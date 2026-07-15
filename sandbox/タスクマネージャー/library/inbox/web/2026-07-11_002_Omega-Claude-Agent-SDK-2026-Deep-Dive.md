# Claude Agent SDK 2026: Deep Dive Guide

- URL: https://o-mega.ai/articles/claude-agent-sdk-the-2026-deep-dive
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-11

## 要約
Claude Agent SDKの2026年詳細技術解説。40の統合ツール・30以上のフックイベント・6種類のパーミッションモード・Agent Teamsに対応。アーキテクチャはAPIラッパーではなくサブプロセスモデル：`claude`バイナリをOS別プロセスとして起動しJSON-RPC via stdin/outで通信。セッションはJSONLトランスクリプトとして`~/.claude/projects/`に永続化。6段階パーミッションモード（default/acceptEdits/plan/auto/dontAsk/bypassPermissions）はマッチャー構文で設定：`Bash(npm run *)`など。CLAUDE.md階層は managed policy → user → project → local の順にロード。Remote Routinesでクラウドスケジューリング・GitHub eventトリガー・HTTPエンドポイントをサポート。サブプロセス設計の優位性：アプリクラッシュでもエージェント状態が保持される。
