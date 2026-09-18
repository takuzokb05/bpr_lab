# Claude Code Plugins完全ガイド【2026年9月正式機能】作成・配布・Marketplace

- URL: https://uravation.com/media/claude-code-plugins-marketplace-complete-guide-2026/
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-09-18

## 投稿内容
Uravationによる2026年9月版Claude Code Plugins完全ガイド。Pluginsは2026年9月時点でbeta表記のない正式機能。Skills/Hooks/MCP設定を一つのパッケージにバンドルして社内・社外に配布できる仕組み。

作成方法: SKILL.md + hooks.json + メタデータをまとめたディレクトリ構造。
配布: settings.jsonへのプラグインパス追加（社内）またはMarketplace公開。
Plugin eval: テストケースファイルで品質保証。
Skillsとの違い: Pluginsはバージョン管理・配布機能あり、Skillsはローカル専用。

## 要約
Claude Code Pluginsの仕組みと実装を解説した日本語ガイド（Uravation 2026年9月版）。SkillsがローカルのCLAUDE.md拡張であるのに対し、Pluginsは配布・バージョン管理ができるパッケージとして機能する。組織内の共通ワークフローをPluginとして標準化→配布するユースケースが強力。Plugin evalによるCI的品質管理が可能になったことで、組織配布前のテストが体系化できる。このリポジトリ（bpr_lab）でも、curate/digest/drop-pickupスキルをPlugin化して管理する選択肢として参考になる。
