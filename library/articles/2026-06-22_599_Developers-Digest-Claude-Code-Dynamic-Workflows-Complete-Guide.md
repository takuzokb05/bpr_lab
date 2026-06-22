# Claude Code Dynamic Workflows 完全ガイド（Developers Digest）

- URL: https://www.developersdigest.tech/blog/claude-code-dynamic-workflows-guide
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-22

## 投稿内容
Complete guide to Claude Code Dynamic Workflows. Two ways to start: ask Claude to "Create a workflow" directly, or enable ultracode mode in /config (sets effort=xhigh, lets Claude auto-decide when to use workflows). Dynamic Workflows are on by default for Max, Team, Enterprise, and API; Pro users enable via /config. Claude dynamically writes orchestration scripts that run tens to hundreds of parallel subagents in a single session, validates results, then presents a final answer. Rate limits doubled across all plans post-SpaceX Colossus deal.

## 要約
Developers DigestによるClaude Code Dynamic Workflows機能の完全技術ガイド。**起動方法2種類**: ①直接「Create a workflow」と指示 ②`/config`でultracodeモードを有効化（effort=xhigh設定、Claudeが自動判断で適用）。**プラン別**: Max/Team/Enterprise/API版はデフォルト有効、Proは手動設定が必要。**動作フロー**: Claude→オーケストレーションスクリプト動的生成→数十〜数百の並列サブエージェント起動→結果集約→検証→最終出力。**ユースケース**: コードベース規模のマイグレーション・大規模リファクタリング・多ファイル横断テスト生成。**現状レート制限**: SpaceXコロッサス提携後に全プランで倍増。**制限**: サブエージェントネスト最大5レベル、バックグラウンドチェーン制限あり。Auto modeとの組み合わせでBedrock/Vertex/Foundry上のOpus 4.7/4.8でも有効。
