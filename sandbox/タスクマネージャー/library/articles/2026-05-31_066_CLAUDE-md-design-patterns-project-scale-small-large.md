# CLAUDE.md設計パターン集：プロジェクト規模別ベストプラクティスと実例

- URL: https://start-link.jp/hubspot-ai/ai/claude-code-practice/claude-code-claudemd-patterns
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-31

## 投稿内容
Start-Link によるCLAUDE.md設計パターン記事。プロジェクト規模別の構成方針と実例を収録。

## 要約
プロジェクト規模ごとのCLAUDE.md設計方針：小規模個人プロジェクトは単一ファイル・シンプル構成（50行以内）、中規模チームはWHAT/WHY/HOW 3層構造 + Skills分離（100〜150行）、大規模組織はルートCLAUDE.md + サブディレクトリCLAUDE.md + 専用Skillsの階層構成（各200行上限）。重要な役割分担：CLAUDE.md は全セッションでロードされる「常時ルール」→ 毎回必要なコンテキスト限定、Skills はオンデマンドロード→ドメイン知識・ワークフロー手順はSkillsへ移行。Hooksとの3層設計思想（CLAUDE.md=助言・Hooks=決定論・Skills=知識）を実例で整理。200行上限を超えると命令が無視される傾向があるため情報密度の最大化が必須。
