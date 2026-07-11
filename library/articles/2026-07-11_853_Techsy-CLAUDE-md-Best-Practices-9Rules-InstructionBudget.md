# CLAUDE.md Best Practices 9ルール: 命令バジェット・4層ロード・決定トライアングル

- URL: https://techsy.io/en/blog/claude-md-best-practices
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-11

## 要約
実践経験から導出したCLAUDE.mdの9つのベストプラクティス（TECHSY, 2026）。

**9つのルール**:
1. コードと同様に扱う（PRでバージョン管理・レビュー）
2. 具体的・テスト可能なルール（曖昧な指針を排除）
3. 各ルールに理由を添える（エッジケース判断のため）
4. ロード階層を意識（global → root → lazy subdirectory → local override）
5. `/init`の出力をそのまま使わずアグレッシブにトリム
6. モノレポでは`@imports`を使いrootファイルを200行以下に維持
7. フレッシュセッションでClaude自身にファイルを要約させてテスト
8. CLAUDE.md・hooks・skillsを正しく使い分ける（hooksは決定論的アクション向け）
9. 複数エージェントCLIを使う場合はAGENTS.mdを使いシンボリックリンクで共有

**ユニークな技術知見**:
- **命令バジェット**: フロンティアモデルは約150〜200命令を信頼性をもって遵守—200行超でcontext rotが発生し遵守率が非線形に低下
- **6つのルール無視原因**: 長さ・曖昧さ・理由なし・コンテキスト圧縮・矛盾・ファイルパス問題
- **4層ロード**: lazy-loadingとsibling isolationでモノレポの肥大化を防止

**決定トライアングル**: CLAUDE.md（助言的・アドバイザリー）vs hooks（決定論的・機械的実行）vs skills（バンドルワークフロー）

**具体的例**: 「クリーンなコードを書け」の代わりに「Server components by default; add 'use client' only when truly needed. Why: we hit 8s LCP last quarter from over-clienting.」
