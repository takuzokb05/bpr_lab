# Tips: Claude CodeではHooksをSKILL.mdに書ける

- URL: https://qiita.com/getty104/items/3d648bf04cfe5a92bc77
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-17

## 要約
Qiita Tipsページ。Claude CodeのHooksをsettings.jsonではなくSKILL.mdのfrontmatterに直接記述できる実装技法を紹介。SKILL.mdの冒頭に`---\nhooks:\n  PostToolUse: ...\n---`と書くだけで同等動作が可能。スキルとフックをひとつのファイルにまとめることで、プロジェクト配布・バージョン管理が容易になるメリットを説明。具体的なyaml構文例とsettings.jsonとの等価性を確認するデバッグ手順付き。
