# Claude Code Skillsの使い方と汎用テンプレート公開

- URL: https://tech-lab.sios.jp/archives/50570
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-04-07

## 要約

SIOS Tech LabによるClaude Code Skills実践ガイドと汎用SKILL.mdテンプレートの公開記事：
- スキルの本質：「業務のやり方をAIに覚えさせ、スラッシュコマンド1つで同品質の仕事を繰り返す」
- 汎用テンプレート：YAMLフロントマター（name/description/when-to-use/tool-calls-allowed）＋コンテンツ部分の標準構成をコピーしてすぐ使える形で公開
- **Gotchasセクションの追加推奨**（Anthropic社内ガイドラインと同じ考え方）：スキルが誤発火・未発火する典型的落とし穴を先に記述
- **Progressive Disclosure設計原則**：必要な時だけ情報ロードしてコンテキスト節約
- 企業内でのスキル標準化テンプレートとして即実装可能

既存スキルへのGotchasセクション追加と本プロジェクトのskills-registryの改善に直接活用できる実践的リソース。
