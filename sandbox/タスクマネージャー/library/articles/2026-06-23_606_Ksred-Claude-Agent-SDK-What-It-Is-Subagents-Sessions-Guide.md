# Claude Agent SDK: Subagents, Sessions and Why It's Worth It

- URL: https://www.ksred.com/the-claude-agent-sdk-what-it-is-and-why-its-worth-understanding/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-23

## 要約
Claude Agent SDKはAnthropicがClaude Codeを動かす同じハーネスを外部開発者に公開したライブラリ（2025年9月にClaude Code SDKから改名）。Python/TypeScript対応、サブエージェント・セッション管理・MCP・ホスト型実行モデルを含む。サブエージェントは(1)並列化と(2)コンテキスト分離の2目的で活用。マネージドエージェントレベルではリードエージェントがジョブを分割し専門サブエージェントへ委任、並列処理後に結果を集約する設計。2026年4月の検索量は14,800（前年比50,000%増）。6月15日以降、Agent SDK利用は別クレジットプール運用（Pro: $20/月、Max 5x: $100/月、Max 20x: $200/月）。実装判断基準「Claude Codeで完結するか vs 外部システム統合が必要か」で選択する。
