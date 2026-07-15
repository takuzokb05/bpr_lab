# Claude Code v2.1.152詳解: /code-review --fixとスキル管理の自動化

- URL: https://dev.classmethod.jp/en/articles/20260524-claude-code-updates-v2-1-152/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 要約
DevelopersIOによるClaude Code v2.1.152アップデート詳解（2026年5月24日リリース）。主要変更点：/code-review --fixがレビュー結果をワーキングツリーに自動適用（再利用・簡素化・効率化のサジェスチョンを直接コードに反映）、/simplifyが/code-review --fixを内部で呼び出す形に統合。バックグラウンドセッションへの/resumeサポート追加（--bgや--agentで起動したセッションがインタラクティブセッションと並んで表示）。スタートアップ75秒ハング問題修正（api.anthropic.comへの接続不可時のサイドチャネルAPIタイムアウトを15秒に短縮）。/usageコマンドでスキル・サブエージェント・MCP別の使用量内訳表示。
