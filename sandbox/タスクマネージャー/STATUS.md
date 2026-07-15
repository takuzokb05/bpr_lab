# STATUS — タスクマネージャー（sandbox統合ハブ）

> **「いま」のスナップショット。** 恒久ルール・ワークフロー定義は `CLAUDE.md` にあるので重複させない。ここには **状態** だけを書く。
> 最終更新: 2026-07-07（新規作成）／ 更新方法: 手動編集
> リポジトリ全体は 1つ上の `../../STATUS.md`（bpr_lab ルート）を参照。

---

## 30秒サマリ

- **sandbox内の複数プロジェクトを統合管理するハブ。** 実体は3つ:
  1. **蔵書管理 `library/`** — Claude Code / AIエコシステムの収集記事 **2715件**、書籍ノート 3件、ダイジェスト 2件。
  2. **情報収集〜キュレーション〜ダイジェストのパイプライン**（スキル9個で駆動）。
  3. **session-review 運用** — 各サブPJのセッション終了時レビューを `.claude/session-review/` に集約（28件蓄積）。
- スキル・エージェント・コマンドは **プロジェクトルートの `.claude/`** に置く（サブディレクトリ配下は Claude Code が認識しない）ルール。
- 現時点で feature-dev パターン（commands/agents 分離）へは移行しない方針（ワークフロー3本・利用者1名のため不要と CLAUDE.md に明記）。

---

## 稼働している仕組み

### スキル（`.claude/skills/` に9個）

| スキル | 用途 |
|---|---|
| **collect-x-articles** | SocialData API で X上の記事・投稿をバルク収集（長文記事・バズ投稿・日英） |
| **drop-pickup** | スマホから投げたリンク（Gmail `[drop]` メール / Slack `#drop`）を回収し drop.md に追記。curate の前処理 |
| **curate** | inbox/ の収集記事とユーザーの drop リンクを精査し articles/ とカタログへ反映 |
| **digest** | articles/ からドメイン別ハイライト・横断知見・アクション提案を単一HTMLダイジェスト化 |
| **adhx** | 会話に x.com/twitter.com リンクが含まれるとき投稿内容を自動取得 |
| **ocr-extract** | Kindle PDF（画像ベース）を Agent Teams 並列OCRでテキスト化（汎用） |
| **reading** | 本のタイトル/Kindle PDF から、ユーザー文脈に落とした実践ガイドを生成し books/ に蓄積 |
| **reading-synth** | OCR済みテキスト＋`library/alter-ego.md` から読書ノートを生成 |
| **research-cc** | Claude Code ベストプラクティスをテーマ別にWeb調査し蔵書目録エントリとして出力 |

### 蔵書（`library/`）

- `articles/` … 収集記事 **2715件**（改変せず原文保存が原則、whiteboard.md 参照）
- `catalog.md` / `catalog-news.md` / `catalog-trading.md` … テーマ別の蔵書目録（追記のみ、既存エントリ削除禁止）
- `books/`（3件）/ `digests/`（2件）/ `inbox/`（未処理: **web 727件（.md）／ X 20 JSONファイル（archive済み102・計約1067ツイート）**。`drop.md` はテンプレのみ）
- `alter-ego.md` … ユーザー最適化のためのペルソナ定義（digest/reading が参照）

### session-review 運用

- `.claude/session-review/` に **28件** のタイムスタンプ付きレビュー（`YYYYMMDD-HHMMSS_元PJ名.md`）。
- SessionEnd フックが自動生成。グローバル CLAUDE.md の規約により、**セッション最初の応答で全件をユーザーへ提示 → 反映指示があれば対応 → 処理済みを個別削除** する運用。
- 直近: `20260703-225025_練習問題.md` / `20260627-000743_昇任試験準備.md` / `20260626-071742_takuz.md`。ai-teams / 介護保険課着任準備 / FX自動取引 由来のものが多い。

### エージェント間共有

- `.claude/whiteboard.md` … Append-only の情報共有ファイル（記事収集の取得ログ、重複注意メモ等）。

### 情報収集ドキュメント（`docs/`）

- `research-claude-code-automation.md` / `research-hooks-mcp.md` / `research-settings-cli.md` / `research-workflow-optimization.md` … Claude Code 自動化・Hooks/MCP・設定CLI・ワークフロー最適化の調査。

---

## 直近の変更

- `library/` は 2026-07-07 更新（`alter-ego.md` が最新）。記事・蔵書の追記が継続。
- リポジトリ全体のコミットは ai-teams に集中しており、タスクマネージャー自体の CLAUDE.md は 2026-06-11 更新（要確認: library/ 配下の更新がコミット済みか未コミットかは未精査）。

---

## 未解決の問い

- **session-review 28件が滞留** している（最古 2026-04-06）。トリアージ・結晶化が追いついていない（親タスクの Step1 が in_progress）。
- `library/inbox/` に未処理が大量滞留（**web 727件・X 20 JSONファイル/計約1067ツイート**、実測 2026-07-07。旧記載「5件」は誤記）。curate による articles/ 反映が保留。
- 「壁打ちのもう一人の自分」PJ（sandbox内・空ディレクトリ）と本ハブの `alter-ego.md` / 壁打ち機能の関係が未整理（要確認: 統合済みか）。
- feature-dev パターンへの移行基準（ワークフロー5本以上 等）に現状は未達。増えた際に再検討。
