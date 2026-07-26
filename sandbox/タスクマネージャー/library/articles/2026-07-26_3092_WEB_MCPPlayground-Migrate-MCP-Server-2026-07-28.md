# Migrate Your MCP Server to the 2026-07-28 Spec

- URL: https://mcpplaygroundonline.com/blog/migrate-mcp-server-2026-07-28-stateless
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-26

## 投稿内容

MCP Playground OnlineによるMCPサーバー2026-07-28仕様移行ガイド。TypeScriptとPythonのコードサンプル付きで実践的な移行手順を解説。

## 要約

- 主な対応箇所4点：initialize ハンドシェイク削除・セッションレス化・_meta フィールド追加・エラーコード変更（-32002→-32602）
- TypeScript・Python双方のコードサンプルでbefore/afterを比較提示
- ステートレス化によりユニットテストの書きやすさが向上（各リクエストが独立するため）
- MCP Tasks拡張を使ってステートフルな長時間実行タスクを代替する方法を解説
- 段階的な移行パス（Feature Flagによる旧仕様との並行サポート）を提供
- Roots・Sampling・Logging非推奨化への対応（12ヶ月の移行期間があるため急ぎ不要）
- MCP Playground Online での新仕様テスト方法も紹介（ローカル不要で即テスト可能）
