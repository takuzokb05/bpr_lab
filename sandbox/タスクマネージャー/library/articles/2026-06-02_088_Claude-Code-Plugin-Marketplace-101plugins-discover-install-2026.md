# Claude Code Plugin Marketplace 2026 — 101プラグイン発見・インストール完全ガイド

- URL: https://www.agensi.io/learn/claude-code-plugin-marketplace-guide
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-02

## 投稿内容
Claude Code Plugins（2026年5月Public Beta）はスキル・サブエージェント・スラッシュコマンド・フック・MCPサーバーを1パッケージにまとめた新形式の拡張機能。

**マーケットプレイスの現状（2026年6月）**
- 公式Anthropicマーケットプレイス: 101プラグイン（Anthropic製33 + パートナー製68）
- コミュニティ全体: 77マーケットプレイス・1,208プラグイン

**対応サービス（パートナープラグイン）**
GitHub, Playwright, Supabase, Figma, Vercel, Linear, Sentry など

**基本操作**
```
/plugin          → Discoverタブでプラグイン検索
/plugin install  → インストール
claude.com/plugins → Webカタログで事前確認
```

**プラグイン vs Skills vs MCPサーバー**
プラグインはこれらを統合した「発見可能な配布フォーマット」。既存のSkills/MCPサーバーもプラグイン形式にラッピングして公開可能。

**開発者向け**
Anthropicの`claude-plugins-community`リポジトリで自動バリデーション・セーフティスクリーニング後に公開できる。

## 要約
Claude Code Plugins機能（2026年5月Public Beta）の完全ガイド。Pluginsはスキル・サブエージェント・スラッシュコマンド・フック・MCPサーバーを1パッケージにまとめた新拡張形式で、マーケットプレイス経由で発見・インストールが可能。
公式マーケットプレイスには101プラグイン（Anthropic製33+パートナー製68：GitHub、Playwright、Supabase、Figma等）が登録済み。
コミュニティ全体では77マーケットプレイス・1,208プラグインが存在（2026年6月時点）。
`/plugin`コマンド→Discoverタブ or claude.com/pluginsで検索・インストール。
既存SkillsやMCPサーバーをプラグイン形式にラッピングして公開することで発見可能性が大幅向上。
日次収集エージェントのSkillや本プロジェクトのカスタムMCPサーバーもPlugin化して再利用性を高められる（P-003/P-011参照）。
