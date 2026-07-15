# Complete Beginner's Guide to Claude Code 2026 — Skills・Agents・Hooks・Plugins・MCP徹底解説

- URL: https://pub.towardsai.net/a-complete-beginners-guide-to-claude-code-skills-agents-hooks-plugins-mcp-085b26b73fdd
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-04

## 投稿内容
A Complete Beginner's Guide to Claude Code (Skills, Agents, Hooks, Plugins, MCP & Cowork) — Towards AI掲載記事（2026年3月）。Claude Code 2026の5層アーキテクチャを系統的に解説する入門〜中級者向け総合ガイド。

**5層アーキテクチャの要点**
- CLAUDE.md: プロジェクトルール・永続コンテキスト（すべてのターンに適用）
- MCP: 外部ツール・データへのブリッジ（USB-Cに相当）
- Skills: SKILL.mdで定義されるプロンプト自動マッチングの再利用ワークフロー
- Hooks: イベント駆動の自動シェルコマンド実行
- Subagents/Agents: 隔離されたサブタスク実行コンテキスト

**意思決定フレームワーク**
「常時必要→CLAUDE.md、手順→Skill、自動実行→Hook」の三分法が明確整理。

**Hooksの実践例（セキュリティゲート）**
preコミット時に認証情報ファイルのdiff確認を行うフックで、Claude Codeを無人稼働させても資格情報の漏洩・誤ったブランチへのプッシュを防止できる。

**2026年の変更点**
- OAuth ログインフロー（2026年2月〜）がデフォルト認証方式に
- claude.ai/codeブラウザ版でローカル環境不要での利用が可能に
- Auto Modeで承認プロンプトをML分類器に置き換え（Proプラン）

## 要約
Claude Code 2026年版の総合入門ガイド（Towards AI）。CLAUDE.md・MCP・Skills・Hooks・Subagentsの5層アーキテクチャと意思決定フレームワーク「常時必要→CLAUDE.md、手順→Skill、自動実行→Hook」を系統的に解説。OAuth認証・ブラウザ版・Auto Mode等2026年の新機能を含む。Hooksによるpreコミット認証情報保護の具体実装例あり。
