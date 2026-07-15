# ムジンケイカク: MCP真の実力とClaude Agent SDKの全貌 — Anthropic公式「Code w/ Claude」動画2本まとめ

- URL: https://mujinkp.co.jp/blog/mcp-claude-agent-sdk-anthropic-official/
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-06-21

## 投稿内容
合同会社ムジンケイカクプロによるAnthropicの「Code w/ Claude」公式動画2本の日本語まとめ記事。MCPとClaude Agent SDKの関係を体系的に整理。

**MCPの5つのプリミティブ（解説）:**
1. **Tools**: 外部APIや実行アクション（例: Slack送信・DB更新）
2. **Prompts**: 再利用可能なプロンプトテンプレート
3. **Resources**: 静的データ・ファイル・ドキュメントへのアクセス
4. **Sampling**: AIからAIへのリクエスト（LLM-to-LLM連携）
5. **Roots**: ファイルシステムへの制御アクセス

**MCPとClaude Agent SDKの役割分担:**
- **MCP**: ツール・データ接続の標準プロトコル（外部サービスとの「USB-C」）
- **Claude Agent SDK**: エージェント実行基盤（ループ管理・コンテキスト制御・エラーハンドリング）

**実装パターン:**
```python
# Agent SDKがMCPを使ってSlack・DB・ブラウザに接続
agent = ClaudeAgent(
    mcp_servers=["slack", "postgres", "browser"],
    model="claude-sonnet-4-6"
)
```

**重要な整理:**
- MCPは「知識」「ツール」を提供するインフラ
- Claude Agent SDKはその上で動くエージェントの「実行エンジン」
- Anthropic公式がこの設計思想を明確に説明したのが今回の動画

**活用方法:**
Anthropic公式チャンネルの「Code w/ Claude」シリーズは英語だが、本記事が日本語で要点を圧縮。MCPサーバー開発者とエージェント開発者の両方に有益。

## 要約
Anthropic公式「Code w/ Claude」動画2本の日本語まとめ。MCPの5プリミティブ（Tools/Prompts/Resources/Sampling/Roots）を解説。MCPとClaude Agent SDKの役割分担を明確化：MCPがツール接続インフラ、SDKがエージェント実行エンジン。Slack・DB・ブラウザへの接続実装例付き。公式設計思想を日本語で最速キャッチアップできるリソース。
