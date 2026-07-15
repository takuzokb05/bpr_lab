# CLAUDE.md Best Practices: 9 Rules That Stop Claude From Ignoring You (2026)

- URL: https://techsy.io/en/blog/claude-md-best-practices
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-11

## 要約
CLAUDE.mdの9つのベストプラクティスを実践経験から導出。①コードと同様に扱う（PRでバージョン管理）②具体的・テスト可能なルール（曖昧な指針を避ける）③なぜを説明（エッジケース判断のために理由が必要）④ロード階層を意識（global→root→lazy subdirectory→local override）⑤`/init`出力をそのまま使わずアグレッシブにトリム⑥モノレポでは`@imports`使用しrootファイルを200行以下に⑦フレッシュセッションでClaude自身に要約させてテスト⑧CLAUDE.md・hooks・skillsの使い分け（hooksは決定論的アクション）⑨複数エージェントCLI環境ではAGENTS.mdを使いシンボリックリンクで共有。ユニークな技術知見：フロンティアモデルは約150〜200命令を信頼性をもって遵守—200行超でcontext rotが発生し遵守率が非線形に低下。6つのルール無視原因（長さ・曖昧さ・理由なし・コンテキスト圧縮・矛盾・ファイルパス問題）を解説。決定トライアングル：CLAUDE.md（助言的）vs hooks（決定論的）vs skills（バンドルワークフロー）。
