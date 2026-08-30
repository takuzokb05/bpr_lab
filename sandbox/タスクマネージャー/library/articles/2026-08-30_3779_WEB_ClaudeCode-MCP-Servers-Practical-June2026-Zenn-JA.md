# Claude Codeで使えるMCPサーバーを試してみた——実用的だったものを整理する

- URL: https://zenn.dev/long910/articles/2026-06-13-mcp-servers-practical
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-08-30

## 投稿内容

Claude Codeで使えるMCPサーバーをいくつか試してみました。実用的だったものを中心に設定方法と活用例をまとめます。
実際に使って効果があったのは次の4つです：GitHub公式MCPサーバー・PostgreSQL MCPサーバー・Playwright（E2E自動化）・Context7（ライブドキュメント取込）。

## 要約

Zenn記事（2026-06-13）によるClaude Code × MCPサーバー実践活用まとめ。試した4系統の評価：
1. **GitHub公式MCPサーバー**: PR作成・Issue検索を自然言語で実行可能。設定ファイルにpersonal access tokenを記述するだけで即使用可能
2. **PostgreSQL MCPサーバー**: DB接続でマイグレーションSQL自動生成。テーブル追加・カラム定義・制約・インデックスを一括生成してくれた
3. **Playwright/Puppeteer**: ブラウザ操作をClaudeが直接制御するE2Eテスト自動化。テストコード生成から実行まで一気通貫
4. **Context7**: 任意ライブラリのライブドキュメントをコンテキストに直接取り込む。ライブラリバージョン違いによるハルシネーション激減
MCP 2026-07-28仕様対応の4大Tier1 SDKが全対応済みで安定稼働を確認。ステートレスプロトコル化で設定がシンプルになった点も好評。
