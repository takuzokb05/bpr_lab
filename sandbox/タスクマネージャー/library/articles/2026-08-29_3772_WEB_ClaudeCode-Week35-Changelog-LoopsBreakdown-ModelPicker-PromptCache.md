# Claude Code Week 35 Changelog: Loops Breakdown・ModelPicker・PromptCache設定

- URL: https://www.gradually.ai/en/changelogs/claude-code/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-29

## 投稿内容

Claude Code Week 35（2026-08-25〜29）のリリース詳細：

**新機能（主要）:**
- `/usage`にLoopsブレイクダウン追加 — ループ実行回数・合計トークン・実行あたりトークン・最終実行時刻を表示。リソース集約タスクの特定が容易に
- `modelPicker`設定でモデルセレクタを順序付き・ラベル付きリストでカスタマイズ可能に
- `promptCacheTtl` / `subagentPromptCacheTtl`設定でプロンプトキャッシュ期間を管理可能
- `modelPricing`マネージド設定で組織契約価格を`/cost`計算に反映（定価でなく実契約価格）
- `/claude-api`スキルにAdmin API coverage更新（organization members・invites・workspaces・API keys・rate limit reports・workload identity federation・CMEK）

**起動/パフォーマンス:**
- サンドボックス・MCP初期化が最初のフレームをブロックしなくなり起動時間改善
- ネイティブインストール・自動更新のダウンロードサイズをzstd圧縮で削減（Linux x64: 340MB→約75MB）

**バグ修正:**
- Linux glibc 2.44以降（Arch Linux・Fedora Rawhide等）のクラッシュ修正（v2.1.245）
- `/config`・`/mcp`・`/skills`・バックグラウンドタスク・`/model`での矢印キー高速入力+Enterが1行上に誤作動する問題を修正
- サブエージェントが最初の呼び出しでモデル404エラーで終了する問題を修正
- `/permissions`にAuto modeタブ追加
- Bash allowルールでサブコマンドの前にワイルドカードがある場合の起動時警告追加

## 要約
Week 35の最大のユーザー価値は「ループ可視化」「モデルコスト最適化」「起動高速化・軽量化」の3点。Loopsブレイクダウンにより、日次収集のような繰り返しタスクのトークン消費を定量的に追跡できるようになる。`modelPricing`マネージド設定はエンタープライズユーザーが契約割引を`/cost`に正確に反映できる実用機能。Linux向けの起動クラッシュ修正と75MBへのダウンサイズ（従来比78%削減）はCI/CD・VPS環境で即効果あり。
