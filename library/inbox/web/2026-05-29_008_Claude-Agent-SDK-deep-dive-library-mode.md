# Claude Agent SDK深掘り: Claude Codeをライブラリとして使う

- URL: https://jidonglab.com/blog/claude-agent-sdk-deep-dive-en/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-29

## 要約
Claude Agent SDKはClaude Codeを動かしているのと同じハーネスをライブラリとして公開したもの。Python（`pip install claude-agent-sdk`）とTypeScript（`npm install @anthropic-ai/claude-agent-sdk`）で利用可能。組み込みツール（ファイルシステム・シェルアクセス）によりボイラープレートを排除し、18のフックイベントによるライフサイクル制御が可能。MCP統合が最も深いフレームワークで、Playwright・Slack・GitHub等のサーバーを1行の設定で接続できる。2026年6月15日からAgent SDK利用は別クレジットプールに分離され、Pro（$20/月相当）・Max 20x（$200/月相当）が追加される。Claude Sonnet 4（claude-sonnet-4-20250514）とOpus 4（claude-opus-4-20250514）は2026年6月15日でAPIからリタイア、Sonnet 4.6・Opus 4.7への移行が必要。Managed Agents webhooks・マルチエージェントオーケストレーション・セルフホストサンドボックスもAWS上のClaude Platformで利用可能。
