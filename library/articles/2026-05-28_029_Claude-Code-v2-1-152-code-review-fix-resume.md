# Claude Code v2.1.152詳解: /code-review --fix自動適用・バックグラウンドセッション/resume

- URL: https://dev.classmethod.jp/en/articles/20260524-claude-code-updates-v2-1-152/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 投稿内容
Claude Code v2.1.152 was released on May 24, 2026. Key new features: /code-review --fix now applies review findings to your working tree after the review, surfacing reuse, simplification, and efficiency suggestions; /simplify now invokes /code-review --fix. Added /resume support for background sessions — sessions started via claude --bg or agent view now appear alongside interactive ones, marked with bg. Fixed startup hanging up to 75s when api.anthropic.com is unreachable. /usage now shows a per-category breakdown including skills, subagents, plugins, and per-MCP-server cost.

## 要約
DevelopersIOによるClaude Code v2.1.152詳解（2026年5月24日リリース）。主要変更点5つ：①/code-review --fixがレビュー結果をワーキングツリーに自動適用（再利用・簡素化・効率化のサジェスチョンを直接コードに反映）、②/simplifyが/code-review --fixを内部で呼び出す形に統合、③バックグラウンドセッションへの/resumeサポート追加（--bgや--agentで起動したセッションがインタラクティブセッションと並んで「bg」マーク付きで表示）、④スタートアップ75秒ハング問題修正（captive portal/ファイアウォール/VPN環境でapi.anthropic.comへの接続不可時のサイドチャネルAPIタイムアウトを15秒に短縮）、⑤/usageコマンドでスキル・サブエージェント・プラグイン・MCP別の詳細使用量内訳表示。
