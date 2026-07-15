# MCP Goes Stateless, Deprecates Sampling（Agent Wars・2026年6月23日）

- URL: https://www.agent-wars.com/news/2026-06-23-mcp-goes-stateless-deprecates-sampling
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-24

## 要約
Agent WarsによるMCP 2026リリース候補解説（2026年6月23日付一次報道）。Sampling非推奨化の背景分析が詳しい：Samplingはサーバーからクライアント（LLM）へのリクエストという「逆方向フロー」で、MCPの主目的（サーバーからツールを提供→クライアントが呼び出す）と設計方向が真逆。これにより実装が複雑化しサーバー側でLLMの判断に依存する危険な設計パターンを生み出していた。代替：通常のツールレスポンスでLLMに必要な情報を返し、クライアント側エージェントが次の行動を決定する標準パターンで同等機能を実現。Extensions framework（reverse-DNS ID方式、ext-*リポジトリで独立バージョニング）の意義：コアプロトコルをスリムに保ちながら機能を拡張可能。MCPサーバー開発者・クライアント実装者は早急に移行計画を立てる必要あり。
