# Claude Code Skillの作り方｜21個運用して分かった設計と育て方（Zenn・JA）

- URL: https://zenn.dev/yamato_snow/articles/3cd6ed9ac340a2
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-26

## 投稿内容
Zennユーザー yamato_snow 氏による「Claude Code Skillの作り方｜21個運用して分かった設計と育て方」。21個のスキルを実際に作成・運用した経験を公開。

## 要約
21個のClaude Code Skillを実際に運用した経験から得た設計・運用知見の公開記事（JA）。**Progressive Disclosure原則の実践**: frontmatter（name/description）は常時コンテキスト在中（〜100語）→SKILL.md本文はスキル起動時のみ読込→scripts/・references/は必要時に実行/参照。**descriptionが9割を決める**: 「このスキルを使うべき場面」を具体的に書かないと自動起動も明示起動も失敗する。曖昧なdescriptionの失敗例と修正例を公開。**21個スキル公開**: コードレビュー・テスト自動生成・PR作成・リリースノート・デプロイチェック・ドキュメント生成等のカテゴリ別スキル一覧とSKILL.md設計判断を解説。**育てる運用哲学**: 「3-5行のシンプルなSKILL.mdで始め、使いながら育てる」アプローチ。完璧を目指した複雑なスキルより、シンプルで動くスキルから始めることを強調。**失敗パターン**: スクリプト化すべき処理をSKILL.md内に記述してコンテキストを浪費・descriptionが広すぎて意図しない場面で起動・references/なしで長文参照をSKILL.mdに埋め込む。
