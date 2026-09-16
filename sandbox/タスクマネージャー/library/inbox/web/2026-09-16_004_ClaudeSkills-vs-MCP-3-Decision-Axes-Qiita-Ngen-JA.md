# Claude Skills vs MCP 使い分け3つの判断軸（Qiita/Ngen）

- URL: https://qiita.com/Ngen/items/30c129861893e6b1a672
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-09-16

## 要約
Qiitaに掲載されたClaude SkillsとMCPの使い分けに関する実践的分析記事（著者: Ngen）。1ヶ月間の実務使用から導き出した3つの判断軸を提示：①「Claude内に置く手順書か/外の世界と繋ぐパイプか」（Skills=内部知識・手順 vs MCP=外部システム接続）②「実行保証が必要か」（保証必要→Hooks、任意→Skills/MCP）③「外部API/DBアクセスが必要か」（必要→MCP、不要→Skills）。具体的な判断フローチャートと実装例（Slackに投稿したいケース→MCP、コードレビュー手順→Skills）を掲載。Skills vs MCP vs Hooks の三者間の関係も整理されており、設計判断の指針として有用。
