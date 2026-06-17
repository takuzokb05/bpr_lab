# Qiita Tips: Claude CodeのHooksをSKILL.mdのfrontmatterに直書きできる（JA）

- URL: https://qiita.com/getty104/items/3d648bf04cfe5a92bc77
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-17

## 要約
Qiita実践Tipsページ。Claude CodeのHooksをsettings.jsonではなくSKILL.mdのfrontmatterに直接記述する技法の公式サポートを確認・共有した記事。`---\nhooks:\n  PostToolUse:\n    - matcher: ...\n      command: ...\n---`という形式でスキルファイル内にhooksを定義できる。メリット：スキルとフックを1ファイルにまとめることでGitバージョン管理が容易、チーム配布がシンプル化、settings.json肥大化を防止。settings.jsonとの等価性の確認手順とデバッグコマンド付き。適用場面：スキルに紐付く専用フック（特定スキル実行時のみ走るPostToolUseなど）の管理に最適。
