# Claude Code CLI: The Complete Guide — Hooks/MCP/Skills/Subagents 56,000語技術リファレンス

- URL: https://blakecrosley.com/guides/claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-09

## 投稿内容
Blake CrosleyによるClaude Code CLIの完全技術リファレンス。v2.1.169（2026年6月8日）対応、56,000語超。「Claude Code as infrastructure」思想に基づく開発ハーネス設計の実践書。

5コアシステムの詳解：
1. **設定**（Configuration）：CLAUDE.md階層（グローバル/プロジェクト/カレントディレクトリ）の読み込み順序と使い分け
2. **パーミッション**（Permissions）：ツール実行の承認フロー・エンタープライズ管理ポリシー設定
3. **フック**（Hooks）：25以上のライフサイクルポイント（UserPromptSubmit・PreToolUse等）での決定論的自動化
4. **MCP**（Model Context Protocol）：外部ツール・サービスのツールチェーン拡張
5. **サブエージェント**（Subagents）：独立コンテキストの並列探索・Agent tool活用

原則ガイド：「フックはプロンプトではなく必ず実行が必要なもの」「MCPはツールチェーン拡張」「スキルはドメイン専門知識の自動適用」。

v2.1.169新機能の詳細解説：
- `--safe-mode`（全カスタマイズ無効トラブルシューティング）
- `/cd`（プロンプトキャッシュ保持ディレクトリ変更）
- `disableBundledSkills`（バンドルスキル非表示）

## 要約
Claude Code CLIを徹底的に解説した56,000語の技術リファレンス。v2.1.169完全対応。5コアシステムの原則的な使い分けから実装例まで網羅。Claude Code as infrastructureという思想に基づく開発ハーネス設計の総括参考書として、Claude Code本番利用者向けの必読リソース。
