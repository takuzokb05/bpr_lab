# PROPOSALS.md

収集記事を横断分析して得られた反映提案。
最終更新: 2026-06-17

---

## 2026-05-27 提案

### P-001: CLAUDE.md への反映 — /model コマンドの挙動変更を明記

**根拠記事**: 003 (Claude Code April changelog)
**詳細**: v2.1.xから`/model`コマンドが「現在のセッションのみ」のモデル変更に変更（永続変更ではなくなった）。CLAUDE.mdにモデル設定はセッションスコープであることを記載し、永続変更が必要な場合の手順を記録しておくべき。

**提案アクション**: CLAUDE.md（存在する場合）に以下を追記
```
## Claude Codeバージョン固有の注意事項
- /model コマンドは現在のセッションのみに適用（v2.1.x以降）。永続変更は設定ファイルで行う。
```

---

### P-002: CLAUDE.md への反映 — CLAUDE.md 500語以内・必須項目リスト

**根拠記事**: 004, 005, 018 (CLAUDE.md best practices 複数記事で一致)
**詳細**: 複数の一次情報記事でCLAUDE.mdの推奨構成が一致している：500語以内、含めるべき内容はテックスタック・エントリーポイント・命名規則・build/test/lint コマンド・共通の落とし穴・コーディングスタイル。

**提案アクション**: 本リポジトリのCLAUDE.mdを上記テンプレートに沿って見直し・整備する。

---

### P-003: Skills Registry への反映 — 提案スキル3件

**根拠記事**: 002, 006 (Hooks/Skills使い分け・Qiita Skills20選)

追加検討すべきスキル案:
1. **`/daily-collect`** — 本日次収集エージェントそのものをスキル化（毎日同じプロンプトを書かずに実行可能に）
2. **`/fx-backtest`** — FX自動取引のバックテスト実行スキル（sandbox/FX自動取引/に対応）
3. **`/catalog-update`** — library/catalog.mdの更新・統計再計算スキル

---

### P-004: FX自動取引への反映 — TradingAgents アーキテクチャの採用検討

**根拠記事**: 011 (TradingAgents v0.2.4)
**詳細**: LangGraphベースのマルチエージェントLLMフレームワーク。AAPL対象で+26.62%のパフォーマンス実績、GitHub 51k stars。5層・12エージェント構成でファンダメンタル・センチメント・テクニカルを統合。Claude APIをバックエンドとして使用可能（GPT・Claude・Gemini・Grokをサポート）。

**提案アクション**: sandbox/FX自動取引/ において、TradingAgentsのマルチエージェントアーキテクチャ（特にセンチメント分析エージェント＋テクニカルエージェントの分離）を参考にした設計検討。LLMバックエンドにClaude Opus 4.7を使用することで既存APIキーを活用可能。

---

### P-005: FX自動取引への反映 — MT5+Python+LLM の統合パターン参照

**根拠記事**: 012 (MT5+GPT-4 Python実装 GitHub)
**詳細**: sandbox/FX自動取引/main.py は既にMT5連携が目標。参照実装（Tzigger/MT5_trading_bot）がOHLCデータ分析→GPT-4推奨→注文送信のパイプラインを公開済み。GPT-4部分をClaude Agent SDKに置き換えることで既存実装を転用可能。

**提案アクション**: Tzigger/MT5_trading_bot のコードを参考に、sandbox/FX自動取引/main.py でClaude Agent SDK経由のLLMシグナル生成を実装する。

---

### P-006: 緊急対応 — Anthropic 2026-06-15 課金変更

**根拠記事**: 007 (Anthropic June15課金変更)
**緊急度**: 高（2026-06-15施行まで18日）
**詳細**: claude -p、Claude Code GitHub Actions、Agent SDK呼び出しが従量課金（標準APIリスト価格）に移行。現在サブスクリプションで実行している自動化スクリプトのコスト試算が必要。

**提案アクション**:
1. 現在の利用量（claude -p呼び出し回数、GitHub Actions実行回数）を確認
2. 6月15日以降の月額推定コストを計算
3. 必要に応じてAPI利用量を調整するか、Anthropic Managed Agentsへの移行を検討

---

## 2026-05-28 提案

### P-007: モデルアップグレード — Claude Opus 4.8への移行検討

**根拠記事**: 020 (Claude Opus 4.8リリース)
**詳細**: 本日（2026-05-28）Claude Opus 4.8がリリース。SWE-bench Pro 69.2%（+4.9pt）、コード欠陥見落とし率4分の1、Fast mode 3倍安価・2.5倍高速。価格はOpus 4.7と同額（$5/$25/Mトークン）のため、FX自動売買のLLMバックエンド・日次収集エージェントのモデル指定をOpus 4.8に更新することを検討。P-004（TradingAgentsアーキテクチャ）での使用モデルもOpus 4.8が最適候補。

**提案アクション**:
1. sandbox/FX自動取引/ のLLMバックエンド設定をclaude-opus-4-8に更新
2. CLAUDE.mdのモデル指定セクション（P-001参照）にOpus 4.8のFast modeが高コスパである旨を追記
3. 日次収集エージェントでの推奨モデルをOpus 4.8 Fast modeに変更（速度・コスト両面で優れる）

---

### P-008: Claude Code Routinesで日次収集を自動スケジュール化

**根拠記事**: 023 (Claude Code Routines)
**詳細**: Claude Code Routinesのスケジュールトリガーを使えば、現在手動実行している日次情報収集エージェントをClaude側のクラウドで毎朝自動実行できる。P-003で提案した /daily-collect スキルとの組み合わせが有効。マシンオフ中も実行継続。

**提案アクション**:
1. /daily-collectスキル（P-003）を先に作成
2. Claude Code Routinesでスケジュール設定（毎朝6:00 JST等）
3. GitHub Actionsトリガーと組み合わせて収集結果をmainブランチへ自動プッシュ

---

### P-009: Dynamic Workflowsで並列バックテストの高速化

**根拠記事**: 021 (Claude Code Dynamic Workflows)
**詳細**: Claude Code Dynamic Workflows（研究プレビュー）が本日公開。最大1,000サブエージェントの並列実行が可能。sandbox/FX自動取引/ のバックテストを複数通貨ペア・複数期間で並列実行する際に活用できる。単一線形エージェントループでは時間がかかりすぎるパラメータ最適化探索に特効。

**提案アクション**:
1. Max/Team/EnterpriseプランまたはAPI経由でDynamic Workflowsを有効化
2. FXバックテストの並列実行プロンプト設計（通貨ペア×時間軸のマトリックス）
3. 結果を統合・比較するオーケストレーターエージェントのCLAUDE.md設計

---

## 2026-05-29 提案

### P-010: Skills設計最適化 — SKILL.md肥大化防止（決定論的処理のスクリプト化）

**根拠記事**: 036 (Claude Code Skills設計パターン・playpark.co.jp)
**詳細**: SKILL.mdが312行→42行（87%削減）・月次エラー80%削減を実証した設計パターン。「決定論的処理（日付計算・ファイル確認・JSON生成）はBashスクリプトへ分離し、SKILL.mdにはAI判断が必要なものだけ記述する」原則で実現。bpr_labの日次収集エージェントSkillにも同原則を適用できる。

**提案アクション**:
1. `.claude/skills/`配下の既存Skillsを監査し、スクリプト化可能な決定論的処理を特定
2. `get_next_date.sh`・`detect_mode.sh`・`orchestrate.sh`パターンを参考に分離実装
3. SKILL.md本体を200行以内（理想は100行以内）に削減

---

### P-011: カスタムMCPサーバー開発 — bpr_lab独自データのClaude接続

**根拠記事**: 041 (エブリー社食トレンド分析MCPサーバー自作事例)
**詳細**: FastMCP + データソース（Databricks/Pandas等）でカスタムMCPサーバーを構築し、Claude APIから自然言語でbpr_lab独自データを問い合わせる事例。FXバックテスト結果・MT5取引ログ・戦略パラメータをMCP経由でClaudeに接続すれば、「過去1ヶ月のSR戦略のSharp比を教えて」のような自然言語クエリが可能になる。

**提案アクション**:
1. FastMCP（`pip install fastmcp`）でsandbox/FX自動取引/のバックテスト結果をMCP化
2. ツール設計: `get_backtest_results(strategy, period)`・`get_trade_log(date_range)`・`compare_strategies()`
3. OpenTelemetryで利用状況・エラー率の継続追跡を設定

---

### P-012: 緊急追加 — Claude Sonnet 4 / Opus 4（20250514版）のモデルリタイア対応

**根拠記事**: 040 (Claude Agent SDK deep dive - 課金・モデルリタイア情報)
**緊急度**: 高（2026-06-15まで残り17日）
**詳細**: P-006（課金変更）に加え、`claude-sonnet-4-20250514`と`claude-opus-4-20250514`が2026年6月15日でAPIからリタイア（ハードデプリケーション）。現在どこかでこれらのモデルIDをハードコードしていれば、その日に呼び出しが失敗する。

**提案アクション**:
1. sandbox/FX自動取引/・library/配下のコードで古いモデルIDを検索: `grep -r "sonnet-4-20250514\|opus-4-20250514" .`
2. 発見した場合は`claude-sonnet-4-6`または`claude-opus-4-7`に変更（Opus 4.8も可）
3. P-006のコスト試算も合わせて実施

---

## 2026-05-30 提案

### P-013: FX自動取引への反映 — MetaTrader MCPサーバーの採用検討

**根拠記事**: 057 (MetaTrader MCPサーバー・32ツール・GitHub)
**詳細**: `ariadng/metatrader-mcp-server`はPython 3.10+で動作し、MCP経由でClaude Desktopから「EUR/USDを0.01ロット買う」などの自然言語指示でMT5を操作できる32ツールのオープンソースブリッジ。REST API・WebSocketストリームもサポート。認証情報はローカルマシン上にのみ保持するセキュア設計。sandbox/FX自動取引/の現在のmain.py（MT5連携目標）に対して、MCP経由での操作レイヤー追加が現実的な選択肢となった。

**提案アクション**:
1. `git clone ariadng/metatrader-mcp-server`でローカルセットアップ確認
2. MT5ターミナルのアルゴリズム取引を有効化し、認証情報を`.env.example`に従って設定
3. Claude Desktop経由で基本操作（価格取得・口座確認）をテストしてからシグナル自動化に拡張
4. P-011（カスタムMCPサーバー）と組み合わせた複合MCPアーキテクチャを検討

---

### P-014: FX自動取引への反映 — MQL5+LLM 4層アーキテクチャと信頼度閾値の採用

**根拠記事**: 056 (MQL5+LLM 2026年実用アーキテクチャ・信頼度0.75超で勝率61.7%)
**詳細**: 4層マイクロサービス（データ収集EA→Python/FastAPIミドルウェア→LLM推論→実行ゲートウェイ）構成と信頼度閾値（0.55未満ノーエントリー48.3%勝率、0.75超でフルサイズ61.7%勝率）の定量的実証値が公開された。P-004・P-005をより具体的な実装設計に落とし込む根拠となる。

**提案アクション**:
1. sandbox/FX自動取引/main.py にPython/FastAPIミドルウェア層を追加設計
2. LLMレスポンスのJSONスキーマバリデーション（action・regime・confidence fields）を実装
3. confidence < 0.55 → noTrade、0.55-0.75 → 半サイズ、0.75+ → フルサイズのポジションサイジングロジックを実装
4. 直近5-10決定のステートフルコンテキスト保持を設計に組み込む

---

### P-015: CLAUDE.md改善 — 段階的開示の3層構造への移行

**根拠記事**: 060 (効果的なCLAUDE.mdの書き方・Zenn・命令予算200個の制約)
**詳細**: LLMが一貫して従える命令数はフロンティアモデルで約200個が上限で、命令数増加と共に全命令の遵守率が一律低下する。推奨構造：Layer 1（CLAUDE.md）に必須情報のみ・Layer 2（.claude/rules/）にトピック別分離・Layer 3（Skills）に専門知識。本プロジェクトのCLAUDE.mdが200行・200命令を超えている場合、重要ルールの遵守率が低下している可能性がある。

**提案アクション**:
1. 現在のCLAUDE.mdの行数・命令数を確認（200行以内かチェック）
2. テーマ別（FX自動取引ルール・ライブラリ管理ルール・コーディングスタイル）に.claude/rules/へ分離
3. P-002（CLAUDE.md整備）とP-010（Skill設計最適化）と統合した包括的見直しを実施
4. 削除基準：「削除したらClaudeが間違えるか？」でNOなら削除を徹底

---

### P-016: 開発ワークフロー改善 — Agent ViewとAuto Modeの活用

**根拠記事**: 049 (Claude Code Agent View), 050 (Claude Code Auto Mode)
**詳細**: Agent View（`claude agents`コマンド・2026年5月11日公開）で複数の並列エージェントセッションを一元管理可能になった。Auto Mode（Proプラン展開中）で人間承認プロンプトをML分類器に置き換え、「コーヒーブレイクで離席できる」水準の自律度を実現。日次収集エージェント（P-003・P-008）やFXバックテスト並列実行（P-009）との組み合わせで大幅な効率向上が見込める。

**提案アクション**:
1. Claude ProプランでAuto Modeを有効化し、日次収集エージェント実行時に試用
2. バックグラウンドセッション（`claude --bg`）で並列タスクを起動し、Agent Viewで一元監視
3. P-008（Routines自動スケジュール）と組み合わせ、完全自律の日次収集フローを構築

---

### P-017: MCPエコシステム対応 — 2026-07-28仕様RC破壊的変更の移行計画

**根拠記事**: 053 (MCP 2026-07-28仕様RC・ステートレス化・廃止ポリシー)
**詳細**: MCP次期仕様（最終版2026-07-28公開予定）でRoots・Sampling・Loggingが非推奨化（12ヶ月以上の移行期間付き）。ステートレス化によりセッション管理アーキテクチャの変更が必要になるMCPサーバーが存在する可能性がある。P-011（カスタムMCPサーバー）・P-013（MetaTrader MCPサーバー）の実装はRC仕様に基づいて設計すべき。

**提案アクション**:
1. 現在使用中のMCPサーバー一覧を確認し、Roots/Sampling/Logging使用有無を調査
2. 新規MCPサーバー実装（P-011・P-013）は2026-07-28 RC仕様準拠で設計
3. 2026年7月28日の最終版公開後、SDK更新と合わせて既存設定を検証

---

## 2026-05-31 提案

### P-018: Hooksドキュメント更新 — 27イベントへの参照修正

**根拠記事**: 062 (Claude Code Hooks完全リファレンス2026)
**詳細**: 2026年5月時点でClaude Code Hooksのライフサイクルイベントは**27種類**に拡大（旧情報「18種類」は2025年時点の数値）。SessionStart・UserPromptSubmit・PreToolUse・PostToolUseを含む27イベントと、Command/Prompt/Agent/Notification/Validationの5ハンドラー型が利用可能。終了コード0/1/2のセマンティクスが明確化され、ブロッキング（コード2）はPreToolUseのみ有効。

**提案アクション**:
1. CLAUDE.md・.claude/rules/ 内の「Hooks 18イベント」等の古い参照を「27イベント」に更新
2. PreToolUse ブロッキング（終了コード2）を活用したセキュリティゲートをHooksに追加
3. Agent hooksをCI/CDパイプライン統合に活用する設計パターンを.claude/rules/hooks.mdに記録

---

### P-019: Routines /schedule 運用Fix — CLAUDE.md にブランチ設定を明記

**根拠記事**: 064 (Claude Code Routines /schedule ブランチ問題)
**詳細**: Claude Code Routinesの/scheduleトリガーを使用するとPRがmainではなくclaude/プレフィックスブランチにプッシュされる既知の挙動がある。CLAUDE.md または Routine定義ファイルに明示的なブランチ設定を記述することで回避可能。P-008（Routines自動スケジュール化）実装時に必ずこの問題に遭遇する。

**提案アクション**:
1. CLAUDE.md に「Routinesは`branch: main`を明示しないとclaude/ブランチへプッシュする」警告を追記
2. P-008実装時のRoutine定義ファイルに `branch: main` を必ず含める
3. GitHubリポジトリの保護ブランチ設定でclaude/系ブランチのPRマージポリシーを確認

---

### P-020: FX自動取引 — TrustTrade式「選択的コンセンサス」のシグナル生成への適用

**根拠記事**: 069 (Agentic Trading arxiv:2605.19337), 070 (TrustTrade arxiv:2603.22567)
**詳細**: TrustTrade論文（2026年3月）が提案する「選択的コンセンサス」機構は、複数LLMエージェントの意見を信頼スコアで重み付けして統合する手法。P-004（TradingAgentsアーキテクチャ）のマルチエージェント設計に組み込むことで、全エージェント均等統合よりも決定品質が向上する。P-014（MQL5+LLM 4層アーキテクチャ）のconfidence閾値と組み合わせると相乗効果が期待できる。

**提案アクション**:
1. sandbox/FX自動取引/ のマルチエージェント設計において、各エージェント（テクニカル・センチメント・ファンダメンタル）に信頼スコアを付与する仕組みを設計
2. 過去の正答率（バックテスト実績）に基づいて信頼スコアを動的更新するアダプタを実装
3. 信頼スコア加重平均がP-014の閾値（0.55/0.75）を下回る場合はノーエントリーとするロジックを追加

---

## 2026-06-01 提案

### P-021: 期間限定50%増枠を活用 — P-009並列バックテスト・P-016Auto Mode積極実行

**根拠記事**: 073 (Claude Code 週次制限50%増加・7月13日まで)
**詳細**: 2026年7月13日まで週次利用制限が1.5倍・短期ウィンドウが2倍に拡大されている（価格据え置き）。P-009（Dynamic Workflowsでの並列バックテスト）やP-016（Auto Mode活用）を試すのに最適なタイミング。レート制限を気にせず大量のサブエージェント実行や長時間のバックテスト探索が可能。

**提案アクション**:
1. 7月13日までにP-009（複数通貨ペア×複数期間の並列バックテスト）を実施
2. Auto Mode（P-016）で日次収集エージェントの完全自律実行をテスト
3. Subagents（P-075参照: 4-8並列worktreeが安定稼働）で並列タスクをフル活用
4. 7月14日以降にデフォルト制限に戻ることを想定し、効率化された手法を7月13日までに確立

---

### P-022: builder.io 50 Tipsから即採用すべき設定 — エイリアス・1Mコンテキスト・remote-control

**根拠記事**: 074 (builder.io 50 Claude Code Tips)
**詳細**: builder.io の50 Tipsのうち即座に生産性向上に直結する設定が複数ある。特に `cc` エイリアスでパーミッションプロンプト全スキップ、`/model opus[1m]`または `sonnet[1m]` で1Mコンテキストをセッション中に切替可能、`claude remote-control`でiOS/Androidからリモート監視・承認が可能。

**提案アクション**:
1. シェルプロファイル（~/.bashrc等）に `alias cc='claude --dangerously-skip-permissions'` を追加
2. CLAUDE.mdに「大規模ファイル解析時は `/model opus[1m]` でコンテキスト拡張を検討」を追記
3. `claude remote-control` の使い方をCLAUDE.mdまたは.claude/skills/に記録（長時間タスク監視用）
4. `!git status` / `!npm test` インラインシェルコマンドをワークフローに組み込む

---

### P-023: Subagents設計パターンの本番実装 — 4-8並列worktreeの標準化

**根拠記事**: 075 (Claude Code Subagents 2026 実践ガイド)
**詳細**: 2026年中頃時点で1開発者あたり4〜8並列worktreeが安定稼働、複雑タスクの完了時間50-70%削減の実績が報告されている。YAML定義ファイルによる再利用可能Subagent構成の管理と、`CLAUDE_CODE_SUBAGENT_MODEL` 環境変数によるコスト制御が本番環境のベストプラクティス。bpr_labの日次収集エージェント（4ドメイン並列）やFXバックテスト（複数戦略並列）に直接応用可能。

**提案アクション**:
1. .claude/agents/ ディレクトリに4ドメイン用Subagent YAML定義を作成（claude-code・claude-ecosystem・ai-trading・ai-news各専門エージェント）
2. `CLAUDE_CODE_SUBAGENT_MODEL=claude-haiku-4-5` 環境変数でサブエージェントコストを抑制
3. Fork mode（`CLAUDE_CODE_FORK_SUBAGENT=1`）でプロンプトキャッシュ共有を試験適用
4. 並列実行で週次制限を効率使用（P-021との組み合わせ）

---

### P-024: FX自動取引LLMバックエンド選択更新 — GPT-5.5 vs Gemini 3.5 Flash vs Claude Opus 4.8

**根拠記事**: 076 (GPT-5.5), 077 (Gemini 3.5 Flash)
**詳細**: 本日時点での主要フロンティアLLMの選択肢が整理できた。
- GPT-5.5: $5/$30/Mトークン、Terminal-Bench 82.7%。エージェント型コーディング強、コスト高。
- Gemini 3.5 Flash: $1.50/$9/Mトークン、Terminal-Bench 76.2%。コスト効率最高、1Mコンテキスト。
- Claude Opus 4.8（既存）: $5/$25/Mトークン、1Mコンテキスト、最高コーディング精度。
FX自動売買の構成（P-014の4層アーキテクチャ）において、Gemini 3.5 FlashはCost-sensitive層（テクニカル分析・データ前処理）、Claude Opus 4.8はHigh-value判断層（最終シグナル統合）という役割分担が最適候補。

**提案アクション**:
1. sandbox/FX自動取引/ のLLM呼び出し設定に「tier別LLMルーティング」を設計
2. 低信頼度・高頻度のデータ前処理にGemini 3.5 Flash（$1.50/Mで約3.3倍コスト削減）を割り当て
3. 最終判断（P-014の0.75超フルサイズエントリー条件）にのみClaude Opus 4.8を使用するルーティング実装

---

### P-025: FX自動取引エージェントへのHITL設計追加 — 日本AI事業者ガイドライン1.2版準拠

**根拠記事**: 078 (日本AI事業者ガイドライン1.2版)
**詳細**: 2026年3月31日公表のAI事業者ガイドライン1.2版でAIエージェントの外部アクションにHITL（Human-in-the-Loop）設計が義務化された（リスクベース段階的監視許容）。sandbox/FX自動取引/ は実資金を扱うエージェントであり、特に「外部アクション（売買注文送信）」にHITL設計が求められる。P-014（信頼度閾値）との組み合わせで、閾値ギリギリのケースは人間確認を挿入する設計が法令準拠かつリスク管理上有効。

**提案アクション**:
1. sandbox/FX自動取引/ に HITL checkpoint を追加: confidence 0.55-0.75 の中間帯は `input()` または通知待ちで人間確認を要求
2. ログ設計: AI判断・人間判断・最終取引の全履歴をトレーサブルに記録（ガイドライン1.2版のトレーサビリティ要件対応）
3. CLAUDE.mdのFX自動取引セクションに「日本AI事業者ガイドライン1.2版 HITL要件」を注記追加

---

### P-026: FX自動取引 — 3ヶ月実験の教訓をシステム設計に反映

**根拠記事**: 085 (AIトレーディングエージェント3ヶ月監視レポート)
**詳細**: 実際にLLMベーストレーディングエージェントを3ヶ月運用した第一人称レポートから得られた設計上の教訓: ①LLMの強みはニュース・感情分析・定性判断であり、短期価格予測は弱い。②バックテスト結果と実取引のパフォーマンス乖離が大きい（スリッページ・手数料・レイテンシ未考慮が原因）。③完全自律は現時点で限界があり、補助役割として使うべき。P-004・P-014・P-025の設計方針と整合しており、今後の開発優先度の根拠として活用できる。

**提案アクション**:
1. sandbox/FX自動取引/ のバックテスト設定にリアルスプレッド・スリッページ（pips）・コミッション・最大レイテンシを必ず含める
2. LLMシグナルの用途を「センチメント分析・ニュースフィルタリング」に絞り、エントリー/エグジットの最終判断はルールベースロジックに委ねる設計変更を検討
3. 毎月の実取引結果とバックテスト結果を比較する「乖離分析レポート」をSkill化（P-003のSkill提案群に追加）

---

## 2026-06-02 提案

### P-027: Context7 + rtkプラグインを日次収集エージェントに導入 — トークン節約

**根拠記事**: 098 (Best Claude Code Plugins tested), 099 (10 productivity workflows)
**詳細**: Context7プラグインは`/plugin install context7`でインストール後、Claude CodeがライブラリドキュメントをWebFetchせずにバージョン固定で参照できる。rtkはCLI出力をLLMコンテキストに入る前にフィルタリング・圧縮するツール。本プロジェクトの日次収集エージェントではWebSearch・WebFetchの結果がコンテキストを大量消費しており、両ツールの導入でコスト削減効果が見込める。Context7は「追加コンテキスト最小・精度向上最大」の最高ROIプラグインと評価されている。

**提案アクション**:
1. `/plugin install context7` でContext7プラグインをインストール
2. `pip install rtk` でrtkをインストールし、Bashコマンドの出力を事前圧縮するラッパーをHooksに設定
3. 日次収集エージェントのWebSearch後の出力をrtkでフィルタリングするプリプロセスを追加
4. Claude APIやAnthropicSDKのドキュメント参照をContext7経由に切り替え

---

### P-028: CLAUDE.md @インポート構文で3層構造への移行

**根拠記事**: 093 (CLAUDE.md Best Practices Ultimate Guide 2026 - amitray)
**詳細**: P-015（段階的開示3層構造）・P-002（CLAUDE.md整備）に対して、amitrayガイドの`@インポート構文`による具体的な実装方法が明確になった。CLAUDE.md本体（500語以内）→`.claude/rules/fx-trading.md`・`.claude/rules/library.md`・`.claude/rules/coding-style.md`へのインポートで、命令数を200以内に維持しながらトピック別詳細を保持できる。

**提案アクション**:
1. 現在のCLAUDE.md を監査し、FX自動取引・ライブラリ管理・コーディングスタイルの3カテゴリに分類
2. `.claude/rules/fx-trading.md`・`.claude/rules/library.md`・`.claude/rules/coding-style.md` を作成して移動
3. CLAUDE.md本体に `@.claude/rules/fx-trading.md` 等のインポート行を追加
4. CLAUDE.md本体が500語以内・削除基準「削除してもClaudeが間違えないなら削除」で精査

---

### P-029: TradingAgents v0.2.0でClaude 4.xバックエンドの実動テスト

**根拠記事**: 096 (TradingAgents Python tutorial - algoinsights)
**詳細**: TradingAgents v0.2.0（2026年2月）でClaude 4.x系（Opus 4.8等）をバックエンドLLMとして直接指定できるようになった。P-004（TradingAgentsアーキテクチャ採用）の実行環境として既存のAnthropicAPIキーを使ってローカルテストが可能。`pip install tradingagents`で環境構築でき、sandbox/FX自動取引/の概念実証として7エージェント構成を試せる。

**提案アクション**:
1. `pip install tradingagents` で環境構築
2. `ANTHROPIC_API_KEY` を設定してClaude Opus 4.8バックエンドでAAPL等で動作確認
3. FX通貨ペア（EUR/USD等）でのシグナル生成をテストし、P-014（信頼度閾値）のconfidence出力を確認
4. バックテスト結果のSharp比・ドローダウンを検証し、統計的信頼性を評価

---

### P-030: Quant AI Agents MT5のFastAPIアーキテクチャを sandbox/FX自動取引/ に適用

**根拠記事**: 095 (Quant AI Agents MT5 setup guide - mql5.com)
**詳細**: MT5ブリッジEA→Python FastAPI→LLM層のアーキテクチャが完全に公開された。出力JSONは`{signal, confidence, sl, tp, lot}`形式でP-014の信頼度閾値と完全互換。sandbox/FX自動取引/main.pyの現状（MT5連携目標）に対して、FastAPIサーバー追加→ブリッジEAアタッチの2ステップで実動テスト環境を構築できる。P-013（MetaTrader MCPサーバー）と組み合わせることでClaude Desktop→MT5の完全な自然言語制御パイプラインも実現可能。

**提案アクション**:
1. `pip install fastapi uvicorn anthropic` で環境構築
2. sandbox/FX自動取引/server.py として LLMシグナル生成FastAPIサーバーを実装（P-014の信頼度閾値ロジック込み）
3. MT5デモ口座でブリッジEAをアタッチし、Paperトレードモードで動作確認
4. P-025（HITL設計）のcheckpoint（confidence 0.55-0.75の中間帯で人間確認）を組み込む

---

### P-031: /ultrareview をFX自動取引コードのリリース前チェックに採用

**根拠記事**: 089 (Claude Code /ultrareview cloud agents)
**詳細**: /ultrareviewは5-20並列エージェントがバグを独立再現検証するクラウドレビューシステム。sandbox/FX自動取引/のコードは実資金を扱うためセキュリティ・ロジックバグのリスクが高く、特に`server.py`・`main.py`・注文送信ロジックのレビューに/ultrareviewが適している。`/ultrareview --pr <番号>`で特定PRを対象にできる。

**提案アクション**:
1. FX自動取引コードの主要機能実装後、`/ultrareview`でリリース前チェックを実施
2. 特に競合状態（注文の重複送信）・入力バリデーション（sl/tp/lot値の検証）・エラーハンドリングを重点的に検査
3. /ultrareviewの結果をPRコメントとして記録し、修正後に再実行して確認
4. Pro/Max/Team/Enterprise プランで利用可能。現在のプランを確認してから利用開始

---

## 2026-06-03 追加提案

---

### P-032: Hooks の `mcp_tool` ハンドラーをシグナル品質チェックに活用

**根拠記事**: 100 (Claude Code Hooks 完全2026リファレンス)
**詳細**: v2.1.141+でHooksハンドラーに `mcp_tool` タイプが追加された。これは既に接続済みのMCPサーバーのツールをhookから直接呼び出せる機能で、P-011（FastMCP FXバックテストデータ接続）と組み合わせることで、FX取引シグナル生成の`PostToolUse`フックから自動的にバックテスト検証ツールを呼び出すパイプラインが構築できる。例：Trader agentがシグナル出力（PostToolUse）→mcp_toolフックがFXバックテストMCPを呼び出してリアルタイム勝率確認→confidence閾値以下なら次のツール呼び出しをブロック（PreToolUse + exit 2）。

**提案アクション**:
1. settings.jsonに `PostToolUse` フックを追加し、`mcp_tool` ハンドラーでFXバックテストMCPサーバー（P-011）を呼び出す設定を記述
2. P-014の信頼度閾値（0.75+）をHookロジックとして実装し、CLAUDE.md依存から確定論的な実行に移行
3. `PreToolUse` + exit 2でconfidence 0.55未満のシグナルをブロック、0.55-0.75はP-025のHITL確認へルーティング

---

### P-033: TradingAgents v0.2.0 の Claude 4.x ネイティブ対応を FX 取引に活用

**根拠記事**: 108 (TradingAgents 2026 実装チュートリアル)
**詳細**: TradingAgents v0.2.0がClaude 4.x（含むClaude Opus 4.8）をネイティブサポートした。P-004（TradingAgentsアーキテクチャ採用）の実装ブロッカーが解消され、7エージェント構成（Market/Social/News/Fundamentals Analyst + Bull/Bear Researcher + Trader + Risk Manager）をそのままFXペアに適用できる。取引決定ごとに11 LLM呼び出し+20ツール呼び出しのコスト（約$0.5-2/決定）をP-006の課金変更（6/15）後の新クレジット枠で試算した上で実装判断が必要。AAPL累積リターン+26.62%（バイアンドホールド-5.23%対比）の実績はFXへの転用可能性を示唆するが統計的異常値の可能性も指摘あり。

**提案アクション**:
1. `pip install tradingagents` 後、Claude Opus 4.8バックエンドで通貨ペア（EUR/USD）を対象にデモ動作確認
2. 取引頻度・1決定あたりのAPIコスト・Agent SDKクレジット消費量を試算し、P-006（6/15課金変更）後の月次コスト見積もりを算出
3. Bull/Bear Researcherの対立論証パターンをP-014の信頼度閾値と統合（両者の合意スコアがconfidenceとして機能）

---

### P-034: FX 自動売買ボットのローカル LLM 化オプション検討

**根拠記事**: 109 (FX自動売買BotのローカルLLM切替実践)
**詳細**: FX相場稼働中はAPIサービス停止でボットが止まるリスクがある。国内個人開発者がqwen3.5:9b→gemma3:12bに切り替えて本番運用している事例が確認された。ローカルLLM化の3つのメリット：①外部API障害リスクの排除（uptime向上）、②APIコスト削減（Opus 4.8は$75/$150 per 1M tokens）、③取引ロジック・市況データの外部送信回避（セキュリティ）。一方でgpu資源・モデル管理コストが発生。P-033（TradingAgents + Claude 4.x）をメインとしつつ、ローカルLLM（LMStudio/Ollama経由でgemma3:12b or qwen3.5:14b）をフォールバックとする可用性設計が現実的。

**提案アクション**:
1. `ollama run gemma3:12b` でローカルLLMを起動し、FXシグナル生成の精度をClaude Opus 4.8と比較テスト
2. TradingAgentsのLLMプロバイダー設定をClaude API→ローカルOllama APIに切り替えて同一テストケースで精度・レイテンシを測定
3. メインはClaude API（高精度）、フォールバックはローカルLLM（可用性）のデュアル構成をsandbox/FX自動取引/config.pyに実装

---

## 2026-06-04 提案

### P-035: 白宮AI大統領令への対応 — FX自動取引ボットの「任意提出対象外」確認と開発方針明記

**根拠記事**: 122 (White House EO AI Innovation Security), 123 (NPR Trump AI safety order)
**詳細**: 2026年6月2日署名の大統領令は「最先端（フロンティア）AIモデル」の開発者に任意の政府提出を求める内容。bpr_labのFX自動取引ボットはフロンティアモデル開発者ではなく「APIユーザー」であるため直接の対象外。ただし、ボットが使用するClaude Opus 4.8はAnthropicが開発するフロンティアモデルであり、Anthropicが政府テストに参加した場合の新安全基準がAPIの利用可能機能・レスポンス形式に影響する可能性がある。また、Colorado州AI法（6月30日施行）はAI「利用者」も対象に含む可能性があり、FX自動売買のような「自動化意思決定システム」が適用範囲に入るか確認が必要。

**提案アクション**:
1. Colorado AI法（6月30日施行）のADMT（Automated Decision-Making Technology）適用範囲を確認し、FX自動売買ボットが対象か法的チェックを実施
2. sandbox/FX自動取引/README.mdに「本システムはClaude API利用者であり、フロンティアモデル開発者規制の直接対象外」という注記と、使用モデル・バージョン・用途を明記
3. P-025（HITL設計）の実装を優先し、「自動化意思決定への人間関与」を記録可能にしておくことでADMT規制への事前対応とする

---

### P-036: Microsoft Agent 365 SDK GA — Claude Agent SDKとの相互運用性検討

**根拠記事**: 118 (Microsoft Agent Framework at BUILD 2026), 124 (Microsoft Build 2026 recap)
**詳細**: Microsoft BUILD 2026でAgent 365 SDK（無料・フレームワーク非依存）がGAとなった。LangChain・OpenAI Agents SDK・LangGraph・Semantic Kernel・Azure AI Foundry と並列に**Claude Agent SDK**もサポートパッケージを提供予定。bpr_labの日次収集エージェントはClaude Agent SDKで構築されているが、Agent 365 SDKが提供するFoundry Agent Service（ホスト型エージェント）・Microsoft IQのWork IQ（M365知識）・Fabric IQ（データグラウンディング）との連携で、Excel/PowerPoint等のM365データをFX分析コンテキストに取り込む経路が開かれた可能性がある。競合ではなく補完的な位置づけとして評価すべき。

**提案アクション**:
1. Agent 365 SDKのClaude Agent SDK向けパッケージを確認し、統合の技術的実現性を調査
2. Microsoft Fabric IQ経由でExcelベースのFXデータ（MT5エクスポート）をClaude Agentのコンテキストに取り込むパイプライン設計を検討
3. 現在のClaude Agent SDK（P-003・P-008のSkills統合）はそのまま維持し、M365連携部分のみAgent 365 SDKを追加する差分アーキテクチャを採用

---

### P-037: FX自動取引の「Bot Pilot」運用体制と月次パフォーマンスレビュースキル化

**根拠記事**: 119 (AI Day Trading Bots Why Most Fail), 121 (Best AI Trading Agents 2026)
**詳細**: 2026年のAI取引ボット研究の共通知見として「48時間放置すれば大半のボットがストップロスに到達」「成功事例はBot Pilot（常時プロンプト調整する専門役割）が存在する」が確認された。Claude Sonnet 4.6は487%・Sharpe 1.94の成績を示したが、これも継続的なパラメータ調整の結果である可能性が高い。sandbox/FX自動取引/ のボットを単純な自動化ではなく「Bot Pilot + 自律実行」のハイブリッドとして設計する必要がある。月次の乖離分析（P-026）と組み合わせたレビュースキルのSkill化が実用的。

**提案アクション**:
1. `.claude/skills/fx-review/SKILL.md` を作成：月次取引結果サマリー・バックテスト乖離分析・戦略パラメータ調整提案の自動生成スキル
2. 週次の `/fx-review` 実行をRoutines（P-008）でスケジュール化し、毎週月曜AM7:00 JSTに自動実行
3. P-025（HITL）のconfidence閾値（0.55-0.75帯）を毎月見直す「Bot Pilot月次調整セッション」をCLAUDE.mdに手順として記録
4. LLMのニュース・感情分析機能（強み）と、ルールベース高頻度執行（弱みを補完）の役割分担をsandbox/FX自動取引/architecture.mdに明文化

---

## 2026-06-05 提案

### P-038: 自己学習型フックの実装 — セッション終了時に学習内容を CLAUDE.md へ自動追記

**根拠記事**: 128 (Dev.to 30 Skills MCPs Self-Learning Hooks)
**詳細**: 実チームの事例で「セッション終了フックがClaudeに学習内容を問い合わせてCLAUDE.mdへ自動追記する」自己学習型フックの有効性が実証された。現状のbpr_labセットアップではセッション間の知識継承は手動であり、知見が蓄積されない課題がある。フックはstdout/stderrとexitコードのみ通信し、シェルコマンドで実装できる（SDK不要）。例: `PostResponse` フックで `claude -p "このセッションで学んだ技術的な知見を箇条書きで出力" >> CLAUDE.md` を実行するパターン。

**提案アクション**:
1. `.claude/settings.json` の `hooks` セクションに `PostResponse` または `Stop` フックを追加し、学習内容抽出プロンプトを設定
2. 追記先はプロジェクトのCLAUDE.mdの「セッション学習ログ」セクション（日付付き）として整理
3. ノイズを防ぐため、追記条件として「ツール呼び出しが3件以上あったセッション」のみ発火させる

---

### P-039: Claude Code 4象限フレームワークによる bpr_lab スキル体系の再整理

**根拠記事**: 135 (GenAI Unplugged Skills/Hooks/Agents Tutorial), 129 (CLAUDE.md Best Practices)
**詳細**: 「CLAUDE.md=メモリ、Skills=ルーティン、Hooks=保証、Agents=委任」の4象限フレームワークが標準的な設計指針として確立した。bpr_labの現在の構成を4象限で棚卸しし、①CLAUDE.mdの肥大化防止（200行以下）、②限定的ワークフローのSkills移行、③自動品質保証のHooks実装、④大規模タスクのAgent委任の4方向で最適化できる。特に日次収集エージェント（本スクリプト）がHooksで自動化できる部分とAgentとして委任すべき部分の境界を明確化すべき。

**提案アクション**:
1. 現在のCLAUDE.md（存在する場合）を4象限で分類し、Skills移行候補を特定
2. `~/.claude/skills/` に「日次収集」「FXシグナル分析」「コードレビュー」「デプロイ」の最低4スキルを整備
3. Hooks候補として「ファイル保存時の命名規則チェック」「コミット前の型チェック実行」「記事追加時のcatalog.md自動更新」を実装

---

### P-040: Claude Opus 4.8 GA確認 — P-033 TradingAgents実装ブロッカー解除

**根拠記事**: 126 (Claude Opus 4.8 公式リリース), 136 (TradingAgents 正式リリース)
**詳細**: Claude Opus 4.8が2026年5月28日に正式GA（Anthropic API・Bedrock・Vertex AI・Microsoft Foundry全対応）。P-033（TradingAgents + Claude 4.x）の実装ブロッカーであった「Claude 4.xの安定GA未確認」が解消された。TradingAgentsのv0.2.0マルチプロバイダー対応と合わせて、今すぐ `tradingagents --llm anthropic --model claude-opus-4-8` の構成でプロトタイプを実装できる。Fast Modeが2.5×速度・3分の1コストで利用可能なため、バックテスト段階ではFast Modeで試算コストを抑えることが推奨される。

**提案アクション**:
1. P-033のアクション1「デモ動作確認」を即時実行：`pip install tradingagents[anthropic]` 後にEUR/USDで動作確認
2. Fast ModeとStandard Modeで同一バックテストを実行し、精度差とコスト差を計測（目標: コスト3分の1で精度95%以上維持）
3. sandbox/FX自動取引/ の `config.py` に `LLM_PROVIDER=anthropic`・`MODEL=claude-opus-4-8`・`USE_FAST_MODE=True`（バックテスト用）を追加

---

### P-041: MCP サーバーのステートレス設計方針への移行準備

**根拠記事**: 134 (MCP Cheat Sheet 2026), 133 (Claude Agent SDK Managed Agents)
**詳細**: MCPの2026年ロードマップ核心は「ステートレス動作への移行」（現行: セッション維持が必須 → 移行後: ステートレスで水平スケーリング可能）。bpr_labでMCPサーバーを新規開発する際（FX自動取引データ取得MCP等）は、今からステートレス設計を採用することで将来の仕様対応コストをゼロにできる。FastMCP 3.0がデコレータ1行でPythonサーバー実装を実現しており、新規MCPの開発コストが大幅低下。加えてMCPトンネル（リサーチプレビュー）によりプライベートネット内MT5サーバーへの安全接続が可能になる見通し。

**提案アクション**:
1. sandbox/FX自動取引/ 向けのMT5データ取得MCPサーバーをFastMCP 3.0でステートレス実装（`@mcp.tool()` デコレータ使用）
2. MCPサーバーはステートをRedis/SQLiteに外出しし、サーバー本体は常にステートレスになるよう設計
3. MCPトンネルの正式リリース後に、VPS上のMT5インスタンスへのMCPアクセス経路を評価


---

## 2026-06-06 提案

### P-042: Dynamic Workflows を日次収集エージェントに適用 — ドメイン並列検索の高速化

**根拠記事**: 145 (Claude Code Dynamic Workflows InfoQ), 146 (5 Workflow Patterns MindStudio)
**詳細**: 現在の日次収集エージェントは4ドメイン×複数クエリを逐次実行しており、全クエリ完了まで5〜10分かかる。Dynamic Workflows（JS オーケストレーションスクリプト）を使えば4ドメインを並列サブエージェントで同時検索し、所要時間を1/4程度に短縮できる見通し。Plan-then-Execute パターン（最もコスト効率が高い）と組み合わせることで、まず収集計画を立ててから並列実行する構成が最適。Max/Team/Enterprise + Claude API で利用可能。トークン消費は逐次実行の1.2〜1.5倍程度になるが、時間短縮の価値が上回る。

**提案アクション**:
1. 日次収集プロンプトをDynamic Workflows対応のJS仕様に書き直す（各ドメイン=独立サブエージェント、最後にmerge集約）
2. `code.claude.com/docs/en/workflows` の仕様を参照し、並列化可能な境界（ドメイン別）とシリアル実行が必要な境界（重複排除・catalog更新）を特定
3. 既存の逐次版と並列版で同一日の収集結果を比較し、品質・コスト・所要時間の差を計測してから本格移行を判断

---

### P-043: TradingAgents 再現性リスクへの対応 — LLMバージョン固定とベースライン検証

**根拠記事**: 154 (TradingAgents Reproducibility ACM ICAIF 2026)
**詳細**: ACM ICAIF 2026論文が「センチメント分析精度がLLMバージョンに強く依存するため再現性リスクがある」と実証した。P-033・P-040（TradingAgents + Claude Opus 4.8）を実装する際、LLMのバージョン変更（例: Opus 4.8 → 4.9）で戦略パフォーマンスが大幅に変動する可能性がある。本番運用では「使用モデルバージョンの固定」と「バージョン変更時のリグレッションテスト」が必須。また、ルックアヘッドバイアスを排除した厳密なバックテスト環境の構築が再現性の前提条件。

**提案アクション**:
1. `sandbox/FX自動取引/config.py` でLLMモデルバージョンを明示固定（`claude-opus-4-8` を浮動バージョンではなく確定バージョンで指定）し、変更時にテストを強制するCI設定を追加
2. バックテスト用のポイント・イン・タイム（PIT）データセットを用意し、ルックアヘッドバイアスを排除した評価環境を構築
3. LLMバージョン変更前後でシャープレシオ・最大ドローダウン・勝率の3指標を自動比較するリグレッションテストスクリプトを実装

---

### P-044: Mercury 2 評価 — FX自動取引の高頻度センチメント分析コスト削減

**根拠記事**: 156 (Mercury 2 Inception Labs 拡散LLM)
**詳細**: Inception LabsのMercury 2（2026年2月GA）は1,000トークン/秒超の生成速度・Claude 4.5 Haikuの1/10コストを実現する拡散アーキテクチャLLM。品質はHaikuクラス相当（Haiku/Flash相当、OpusやGPT-4レベルではない）。FX自動取引でセンチメント分析（ニュースヘッドライン・X投稿の感情スコアリング）をリアルタイム高頻度実行する場合、Opusの高品質な推論が不要なタスクにMercury 2を採用することでコストを90%削減できる可能性がある。OpenAI API互換のため既存コードの変更は最小限。

**提案アクション**:
1. FX自動取引ボットのタスクを「高品質推論が必要なもの（戦略判断・最終売買決定）」と「大量処理が必要なもの（ニュース感情スコアリング・フィルタリング）」に分類
2. 後者にMercury 2 API（`inceptionlabs.ai`）を試験導入し、Claude Haiku と同一テストケースで精度・コスト・レイテンシを比較
3. 精度が許容水準（感情スコア相関>0.85）ならMercury 2を大量処理パスに採用し、戦略判断のみClaudeを使うハイブリッドアーキテクチャに移行

---

### P-045: Claude Code Auto Mode 有効化 と CLAUDE.md 権限設計の見直し

**根拠記事**: 144 (Anthropic Claude Code Auto Mode Engineering Blog)
**詳細**: Anthropicエンジニアリングブログによれば、Auto Modeはルールベースではなくモデルによるリスクスコア評価で動的に権限を制御する。Pro プランはSonnet 4.6、Max/Enterprise は Opus 4.8 で動作。「デストラクティブな操作」（git reset --hard・rm -rf・外部API書き込み等）のみブロックし、通常の開発操作はパーミッション確認なしで進む。現在のbpr_labでは毎回のパーミッション確認が作業を中断しているため、Auto Mode有効化とCLAUDE.md上での「禁止操作明示」のセットアップで大幅に開発速度が向上する見込み。

**提案アクション**:
1. Claude Code設定でAuto Modeを有効化し（`/auto` コマンドまたは設定ファイル）、プロジェクトのCLAUDE.mdに「Auto Mode適用範囲と禁止操作リスト」を明記
2. CLAUDE.mdの「禁止操作」セクションに `git push --force`・`DROP TABLE`・`rm -rf`・本番APIへの直接書き込み等を列挙し、Auto Modeのリスク判定精度を補強
3. Auto Mode有効後に1週間の試用期間を設け、意図しないブロックや意図しない実行が発生していないかログで確認（`~/.claude/logs/`を定期確認）

---

## 2026-06-07 提案

### P-046: Anthropic IPO後の API価格変動リスクを bpr_lab コスト設計に組み込む

**根拠記事**: 160 (Anthropic IPO S-1 機密提出), 168 (Anthropic Q2 2026 初の営業黒字)
**詳細**: AnthropicがSECにS-1を機密提出（2026年6月1日）。評価額$965B・年換算売上$47Bの上場申請企業として、上場後は投資家の期待収益への対応のためAPI価格戦略が変化する可能性がある。一方Q2で初の営業黒字（$559M）を達成しており、AWS/Googleとの大型コンピュート契約（$50B超）が利益率改善の下支えになっている。FX自動取引ボットのコスト試算（P-006）に「API価格+10%・+30%・+50%シナリオ」を追加し、各シナリオでの月次コスト変化をconfig.pyに試算式として実装しておくことを推奨。

**提案アクション**:
1. sandbox/FX自動取引/config.py に `API_COST_MULTIPLIER` 変数を追加し、価格シナリオ切替を1行で対応可能にする
2. README.md に「APIプロバイダーはIPO後価格変動リスク有り。代替（ローカルLLM・P-034）への切替手順を記録」を注記
3. P-006（課金変更）とP-024（tier別LLMルーティング）を組み合わせた月次コスト上限アラートの設計を検討

---

### P-047: SpaceXコンピュート提携による利用制限拡大を FX 並列バックテストに即活用

**根拠記事**: 161 (Anthropic-SpaceX Colossus), 171 (窓の杜 SpaceX JA)
**詳細**: Claude Codeの5時間レート制限が全プランで2倍になった（2026年5月6日施行）。P-021（7月13日まで50%増枠）・P-023（4-8並列worktree）と合わせると、現在がbpr_lab史上で最も高いレート制限を享受できる時期。FXバックテスト（複数通貨ペア×複数戦略の組み合わせ）をこの期間中に集中的に実行し、戦略パラメータの初期最適化を完了させることを推奨。

**提案アクション**:
1. P-009（Dynamic Workflows並列バックテスト）を今週中に着手（7月13日の制限戻りまでに完了目標）
2. 5時間制限2倍＋50%増枠＋並列4-8worktreeの組み合わせでの最大スループットを計算し、バックテスト計画に反映
3. SpaceX Colossus提携の継続期間（発表上は「月内」だが長期化の可能性）を定期的にモニタリング

---

### P-048: Apple Xcode 26.3 統合 → Claude Agent SDK のクロスプラットフォーム活用検討

**根拠記事**: 162 (Apple Xcode 26.3 Claude Agent SDK ネイティブ統合)
**詳細**: Xcode 26.3にClaude Agent SDKがネイティブ統合された（2026年2月3日）。VS Code・JetBrains・Xcodeと主要IDEでの公式統合が揃い、Claude Agent SDKが「IDE非依存のAIエージェント標準」としての地位を確立した。bpr_labのFX自動取引ボット開発がMacOS環境で行われている場合、Xcode経由でのビジュアルプレビュー・クラッシュログ自動解析・ユニットテスト自動実行ループが追加のコスト不要で利用可能になる。

**提案アクション**:
1. 現在のbpr_lab開発環境（OS・IDE）を確認し、Xcode 26.3以降を使用している場合はClaude Agent SDK統合を設定
2. sandbox/FX自動取引/ のPythonコードをXcode Projectに追加し、Xcode PreviewsではなくCrash Loggerとの統合を検討
3. MCP経由のClaude Code CLIからXcode機能にアクセスする設定（Xcode MCP）のセットアップ手順を.claude/rules/ に記録

---

### P-049: 米国連邦AI法案（269ページ）の成立動向を監視 — Colorado AI法 6/30 施行との関係

**根拠記事**: 163 (AIニュース 2026年6月7日), 158 (2026年米国AI規制総覧)
**詳細**: 2026年6月7日、米議会でAI関連の269ページ法案が提出された。この法案は全州AI法を上書きする連邦プリエンプション条項を含む可能性があり、Colorado AI法（2026年6月30日施行・ADMTリスク管理義務）が無効化される可能性がある。P-035（FX自動売買ボットのColorado法適用可能性確認）は、この連邦法案の成立状況次第で対応優先度が変わる。

**提案アクション**:
1. 2026年6月末に連邦AI法案の審議状況を再確認し、Colorado AI法との関係を法的に評価
2. P-035のアクション1（Colorado AI法のADMT適用範囲確認）は6月30日施行前に完了させる（連邦法案が成立するまではColorado法が有効）
3. 連邦AI法案が成立した場合の新規コンプライアンス要件をCLAUDE.mdに更新

---

### P-050: 国産LLM「LLM-jp-4」をFX自動取引のニュース感情分析コスト削減に検討

**根拠記事**: 176 (国産LLM LLM-jp-4 NII オープンソース公開)
**詳細**: 国立情報学研究所（NII）が2026年4月3日に公開した「LLM-jp-4（8B/32B）」はオープンソース・商用利用可能・12兆トークン学習で一部ベンチマークGPT-4o超え。P-034（ローカルLLM化オプション）・P-044（Mercury 2コスト削減）と同様のハイブリッドアーキテクチャの候補として評価可能。日本語ニュースの感情分析に特化した性能を発揮する可能性があり、FXボットの高頻度ニュースフィルタリングレイヤーに適用できれば外部APIコストを大幅削減できる。

**提案アクション**:
1. LLM-jp-4 8Bモデルを`ollama run`または`vLLM`でローカル起動し、日本語FXニュースの感情分析精度をClaude Haiku 4.5と比較テスト
2. P-044（Mercury 2）とLLM-jp-4の精度・コスト・レイテンシを同一テストセットで3モデル比較（Claude Haiku / Mercury 2 / LLM-jp-4）
3. 最優秀モデルをFXボットの「大量処理パス（ニュース感情スコアリング）」に採用し、「高品質推論パス（最終売買判断）」にClaudeを使うアーキテクチャを実装

---

## 2026-06-08 提案

### P-051: Anthropic公式MCP設計術「98.7%トークン削減」を日次収集エージェントのMCP設計に適用

**根拠記事**: 189 (Zenn - Anthropic公式MCPサーバー設計術 98.7%トークン削減)
**詳細**: Anthropic公式リファレンスから逆引きされた設計パターンで「Tool descriptionを簡潔に保つことで98.7%のトークン削減を達成（実測値）」が実証された。日次収集エージェントでは現在WebSearch結果がコンテキストを大量消費している。もし将来MCPサーバーを経由して収集ロジックを実装する場合（P-011参照）、この設計パターンの採用でコストを劇的に削減できる。加えてResourcesプリミティブを活用したURLだけ渡すパターン（P-027のrtk圧縮と補完的）が有効。

**提案アクション**:
1. 日次収集エージェントの各WebSearch結果の出力を「URLのみ→必要時にWebFetch」のパターンに変更し、トークン消費を削減
2. P-011（FastMCP FXバックテストMCPサーバー）の設計時に、Tool description を50文字以内・パラメータを3つ以内に制限するルールをCLAUDE.mdに追記
3. Resourcesプリミティブを活用し、大量データは `resource://backtest/result/{id}` 形式のURIで参照するステートレス設計を採用（P-041との統合）

---

### P-052: 3大AIエージェントSDK比較の知見を bpr_lab のSDK選択方針として明文化

**根拠記事**: 191 (Composio - Claude Agent SDK vs OpenAI vs Google ADK比較)
**詳細**: bpr_labのFX自動取引ボット・日次収集エージェントはClaude Agent SDKをメインSDKとして使用しているが、その選択根拠がドキュメント化されていない。3大SDKの比較知見を踏まえて：Claude Agent SDK = MCP最深統合・ファイルシステム/シェルアクセスビルトイン・サブエージェントネイティブのため、コードベース操作・ローカルファイル処理・MCP統合が中心のbpr_labプロジェクトに最適。ただし6/15以降のAgent SDK課金変更（P-006・P-012参照）後は、コスト感応度の高いタスクにOpenAI Agents SDK（マルチベンダー対応）の部分採用を検討する余地がある。

**提案アクション**:
1. sandbox/FX自動取引/README.md に「SDK選択理由: Claude Agent SDKを採用する根拠（MCP統合・ファイルシステムアクセス・ローカルエージェントパイプライン）」を記録
2. 将来的にOpenAI/Geminiモデルをフォールバックとして追加する場合（P-034・P-024参照）に備え、SDKを抽象化するプロバイダーレイヤーの設計をarchitecture.mdに記載
3. P-006（6/15課金変更）後のAgent SDK月次コストが許容範囲を超えた場合の代替SDK切替手順を.claude/rules/cost-control.mdに記録

---

### P-053: 47本FXロボット実検証レポートの設計方針をサンドボックス評価フレームワークに反映

**根拠記事**: 196 (Medium - 47本FXロボット$11,400損失レポート)
**詳細**: 実際に47本のFXロボットをライブ運用してテストした第一人称レポートから、bpr_labの sandbox/FX自動取引/ に直接適用できる設計原則が得られた：①バックテスト良好→ライブ失敗のパターンは「過剰最適化」が原因（P-043のLLMバージョン固定と同じ根本問題）；②「AI搭載」の大半はラベルのみで実際のLLM活用なし（本プロジェクトはClaude APIを本当に使う差別化があり有利）；③成功ロボットに共通する最大DD 10%以下の厳格なリスク管理。これは P-014（信頼度閾値）・P-025（HITL設計）・P-043（LLMバージョン固定）と整合する実証データとして位置づけられる。

**提案アクション**:
1. sandbox/FX自動取引/evaluation_framework.md を作成し、「最低3ヶ月フォワードテスト必須」「最大DD 10%以内をロボット採用基準」「バックテストとライブの乖離分析を毎月実施（P-026）」の評価基準を明文化
2. P-014（信頼度閾値）を「最大DD 10%以下を維持するための信頼度閾値キャリブレーション」として位置付け、閾値と実際のドローダウンの関係を記録・更新するテーブルをconfigに追加
3. evaluation_framework.md に「LLM本当活用の差別化ポイント（ニュース感情分析・多角的シナリオ分析・非線形判断）」と「LLMが不得意なこと（短期価格予測・ノイズの多い市場での過適応）」を明記し、システム設計の範囲と限界を文書化

---

## 2026-06-09 提案

### P-054: Claude Fable 5モデルアップグレード検討 — agenticコーディング性能でOpus 4.8を+11pt超え

**根拠記事**: 200 (Claude Fable 5 リリース VentureBeat), 201 (Fable 5 ベンチマーク Vellum)
**詳細**: 2026年6月9日リリースのClaude Fable 5はSWE-Bench Pro agentic codingで80.3%（Opus 4.8: 69.2%）を達成。GPT-5.5（58.6%）・Gemini 3.1 Pro（54.2%）を大幅リード。価格はFable 5が$10/$50/Mトークン（Opus 4.8の$5/$25の2倍）。コーディング重視タスク（FX自動取引コード生成・sandbox/FX自動取引/のリファクタリング・バグ修正）では費用対効果がOpus 4.8を上回る可能性がある。ただし高リスクトピックはOpus 4.8へフォールバック（セッション5%未満）。P-007（Opus 4.8アップグレード）・P-040（TradingAgents実装）のモデル選択を見直す必要がある。

**提案アクション**:
1. Claude Fable 5の`claude-fable-5-20260609`（仮）モデルIDをAnthropicドキュメントで確認し、sandbox/FX自動取引/config.pyの `PREMIUM_MODEL` 変数を更新
2. 同一バックテストタスクをOpus 4.8とFable 5で実行し、コーディング品質（コードレビュー自動スコア）と推論時間を比較
3. P-033（TradingAgents + Claude 4.x）でFable 5バックエンドを試験：AAPL等のバックテストでOpus 4.8対比のパフォーマンス差を計測
4. 日次収集エージェント（本スクリプト）でもFable 5を試験し、SIGNAL/NOISE分類精度の変化を記録

---

### P-055: Great American AI Act草案 — Colorado AI法改正後の規制環境変化でP-035・P-049を更新

**根拠記事**: 206 (Great American AI Act FedScoop), 207 (Colorado SB 26-189 TechTimes)
**詳細**: P-035・P-049の前提が変化した。Colorado SB 26-189（2026年5月9日成立）により：(1)旧Colorado AI法（SB24-205）は廃止・置換済み、(2)新法（SB 26-189）は規制対象をADMTに絞り込み・施行日を2027年1月1日へ延期。加えてGAGAIA（Great American AI Act）が6月4日に草案公開され、州法3年プリエンプション条項が含まれる。仮にGAGAIAが成立すればColorado SB 26-189も3年間プリエンプションされる可能性があり、P-035のコンプライアンス判断が流動的になった。現時点での実務的結論：2027年1月1日施行まで余裕があるため、P-025（HITL設計）の実装を優先しつつ連邦法成立動向を監視。

**提案アクション**:
1. P-035・P-049の提案状態を「待機中：連邦GAAIA成立動向監視」にステータス更新
2. CLAUDE.mdのFX自動取引セクションに「使用AIシステムはClaude API利用者（フロンティアモデル開発者ではない）。ADMT規制の直接対象は2027年1月施行のColorado SB 26-189のみ、GAAIA成立で変更の可能性あり」を注記
3. 次回の連邦GAAIA審議状況確認スケジュールを2026年9月末に設定（3年プリエンプション条項の修正・廃止の可能性を含めて評価）

---

### P-056: Claude Code fallbackModel設定をFX自動取引パイプラインに組み込む

**根拠記事**: 209 (Claude Code fallbackModel設定ガイド - AIforAnything)
**詳細**: P-006（529過負荷エラー対策）の具体的実装方法が確立した。v2.1.166+のfallbackModel設定で最大3つのバックアップモデルを設定でき、過負荷時にユーザー操作不要でフォールバック。バックグラウンドセッション（--detach）もフォールバック設定を継承するため、FX自動取引ボットの夜間無人稼働時のAPI障害リスクが低減できる。P-034（ローカルLLMフォールバック）の前段として、まずfallbackModel（Claude Haiku 4.5）でAPI内フォールバックを確立し、それでも失敗する場合（プラットフォーム全体障害）にローカルLLMへ委譲するという2段階可用性設計が現実的。

**提案アクション**:
1. `sandbox/FX自動取引/.claude/settings.json`（または相当する設定）に `"fallbackModel": ["claude-haiku-4-5-20251001"]` を追加
2. P-024（tier別LLMルーティング）と統合：高品質判断レイヤーは `claude-fable-5` (or `claude-opus-4-8`) をprimary・`claude-sonnet-4-6` をfallback1・`claude-haiku-4-5` をfallback2に設定
3. バックグラウンドセッション（`claude --bg`）で稼働中のFX取引エージェントがfallbackModelを正しく継承するか、ステージング環境で意図的に529エラーを発生させて確認

---

### P-057: Anthropic社員活用術の「サブエージェント利用判断基準」をCLAUDE.mdに明記

**根拠記事**: 210 (Anthropic社員Claude Code活用術8選 Zenn)
**詳細**: Anthropic公式レポート由来の「10ファイル以上の探索 or 3つ以上の独立作業 → サブエージェント使用シグナル」という定量的基準はCLAUDE.mdの運用ルールとして採用できる。現在のbpr_labでは日次収集エージェント（4ドメイン）がこの基準に合致しており、P-023（4-8並列worktreeの標準化）・P-042（Dynamic Workflows適用）の実装優先度を高める根拠となる。また「コンテキストエンジニアリング（構造設計重視）」というパラダイムシフトはCLAUDE.mdの設計思想に直結する。

**提案アクション**:
1. CLAUDE.mdに「サブエージェント使用シグナル：10ファイル超の探索が必要な場合 または 3つ以上の独立作業を含む場合（Anthropic公式基準2026）」を追記
2. P-023のSubagent YAML定義作成時に上記基準を組み込んだオーケストレーターエージェントの判断ロジックを設計
3. 「成功基準の先行定義」（例：「テスト全通過」「このAPIレスポンスがこの形式」）をClaude Code使用時の標準プロセスとしてCLAUDE.mdに追記（ステップ指示よりも成果物記述が効果的）

---

### P-058: Claude Agent SDK 6/15請求変更への対応準備

**根拠記事**: 219 (Claude Agent SDK Complete Guide - Hidekazu Konishi)
**詳細**: 2026年6月15日より、Claude Agent SDK / `claude -p` / Claude Code GitHub Actions / 第三者エージェントがサブスクリプション枠から切り離され、専用クレジットプール（フルAPIレート課金）に移行。bpr_labの日次収集エージェントが `claude -p` 経由で実行されている場合、6/15以降は費用が発生するクレジットプールから引かれる。

**提案アクション**:
1. bpr_labの日次収集ワークフローが `claude -p` を使っているか確認し、使っている場合はMonthlyクレジット上限を設定（Claude設定 → Agent SDK Credit Limitから設定可能）
2. FX自動取引サンドボックスがAgent SDKを使う場合は同様に上限設定を検討
3. CLAUDE.mdに「Agent SDK / claude -p 実行は6/15以降クレジットプール消費（フルAPIレート）。バッチ処理はMessage Batches API優先で30%コスト削減」を注記

---

### P-059: FX自動取引へのONNX/MT5内蔵NN実行パターン採用検討

**根拠記事**: 220 (AI Trading Tools 2026 - Ventureburn)
**詳細**: MT5のONNX統合を使えば、Python外部スクリプト不要でEA（MQL5）内から直接ニューラルネットワークモデルを実行できる。現在のsandbox/FX自動取引/がPython+ZeroMQ/REST APIブリッジでMT5と通信する構成を採用している場合、高頻度の判断部分（テクニカル指標計算など）はONNX経由でEA内蔵に移行することでレイテンシ削減が可能。LLMセンチメント分析（低頻度・高コスト）は引き続きPython側でClaude APIを呼び出す2層構造が現実的。

**提案アクション**:
1. `sandbox/FX自動取引/` の現行アーキテクチャを確認し、EA内ONNX推論とPython側LLM分析の責任分界点を設計
2. テクニカル判断（エントリー/エグジット条件）はONNX化、センチメント・ファンダメンタル判断はClaude API（claude-haiku-4-5 軽量モデル）に割り当てる「コスト最適2層」構成を文書化
3. P-005（MT5+Python+LLM統合パターン）と統合した実装ロードマップを更新

---

## 2026-06-11 提案

### P-061: MCP RC breaking changes 実装移行 — P-017補強・エラーコード変更対応

**根拠記事**: 223 (MCP 2026-07-28 RC 公式ブログ), 208 (Medium MCP RC解説)
**詳細**: P-017で「RC仕様準拠設計」を提案していたが、2026-07-28の公式RCブログポストで具体的なbreaking changesが確定した。最も影響が大きいのはエラーコード変更（-32002→-32602）と初期化ハンドシェイク廃止。現在稼働中・開発中のMCPクライアントコード（P-011のバックテストMCPサーバー、P-013のMetaTrader MCPサーバー）がこれらの変更でサイレントに壊れる可能性がある。移行期間付きなので緊急対応は不要だが、新規実装はRC仕様で始めるべき。

**提案アクション**:
1. 現在のコードベースで `-32002` エラーコードを参照している箇所を検索（`grep -r "\-32002" .`）し、`-32602` への移行計画を立案
2. P-011・P-013のMCPサーバー実装開始時にステートレス設計を前提とし、初期化ハンドシェイクを持ち込まない
3. 2026年7月28日の最終仕様公開後2週間以内に既存MCPツール設定の互換性検証を実施するスケジュールをCLAUDE.mdに記録

---

### P-062: TradingAgents実装のオーケストレーター選定 — LangGraph 0.4を正式推奨

**根拠記事**: 225 (LangGraph vs AutoGen 2026 DEV Community), 226 (TradingAgents Docker tutorial)
**詳細**: 2026年の本番AIエージェントフレームワーク比較記事により、P-033（TradingAgents + Claude 4.x実装）のオーケストレーター選定に明確な根拠が得られた。TradingAgentsはLangGraphベースで実装されており（P-004で確認済み）、2026年の比較研究でもLangGraph 0.4以降が「監査可能性・チェックポイント・Human承認ゲート」の観点で本番最適と評価された。AutoGenは研究プロトタイピングに向くが、実資金を扱うFXボット（P-025 HITL必須）にはLangGraphが適合する。

**提案アクション**:
1. P-033のTradingAgents実装にあたり `pip install langraph>=0.4` を明示的に要件として記録
2. FXシグナル生成の各ステップ（データ取得→分析→シグナル→HITL確認→執行）をLangGraphノードとして設計し、各ノード間にP-025のHITLチェックポイントを挿入
3. LangSmithとの統合（無料Tier利用可）でエージェントの意思決定プロセスを追跡し、P-037（月次パフォーマンスレビュー）のデータソースとして活用

---

### P-063: MT5/MQL5コード生成にはClaude Opusが最高品質 — FX開発モデル選択の根拠確定

**根拠記事**: 230 (QuantLabs LLM Showdown 2026), 155 (FX自動売買LLM活用実験記録 JA)
**詳細**: QuantLabsの比較実験でClaude（Opus系）がMT5/MQL5コード生成において「コード構造・ドキュメント品質・MQL5特有構文エラー率」で最高評価を得た（2026年）。特にPython-MQL5橋渡しコードとZeroMQブリッジ実装でGPT-5.5・DeepSeek R3を上回る完成度。一方でDeepSeek R3はOpusの90%品質をコストの約3分の1で実現するため、コスト重視の反復開発フェーズに適している。この実証データはP-024（tier別LLMルーティング）の具体的な実装根拠となる。

**提案アクション**:
1. `sandbox/FX自動取引/` のMQL5コード生成・レビュータスクには `claude-fable-5` または `claude-opus-4-8` を指定（P-063根拠：MT5特有構文エラー最小）
2. P-024のtier設計を更新：「MQL5/MT5コード生成 → Claude Opus」「ニュースセンチメントスコアリング → DeepSeek R3またはMercury 2」の役割分担を config.py に明記
3. QuantLabsのプロンプトテンプレート（取引ロジック記述フォーマット）を参考に、`.claude/skills/fx-codegen/SKILL.md` のプロンプト設計を最適化

---

### P-060: Skills SKILL.md descriptionの自然言語最適化

**根拠記事**: 216 (100 Claude Skills試用 - PyCoach), 217 (70+ Skills自作 - PyCoach)
**詳細**: 100件・70件の大規模Skills実験から得られた知見：「SKILL.mdのdescriptionを自然言語で具体的に書くほど、自動トリガー精度が上がる」「スキルは小さく・焦点を絞って作る」「チーム共有はgitサブモジュールかnpmパッケージが有効」。bpr_labの既存スキル（.claude/skills/配下）のdescriptionが曖昧・短い場合、自動トリガーが外れてスキルが活用されていない可能性がある。

**提案アクション**:
1. bpr_labの `.claude/skills/*/SKILL.md` を一覧し、各スキルのdescriptionを「いつ・何のために使うか」を具体的に記した自然言語文に書き直す
2. 1スキル1責務の原則で肥大化しているスキルを分割（特にcurateスキルなど複数処理を含むもの）
3. 更新後、3回の日次収集で自動トリガー率を測定し効果を確認

---

## 2026-06-12 提案

### P-064: Claude Fable 5 本番採用 + セーフガード透明性ポリシー対応

**根拠記事**: 235 (Claude Fable 5 公式リリース), 237 (秘密妨害ルール撤回), 242 (TrueFoundry完全ガイド)
**詳細**: Claude Fable 5（claude-fable-5-20260609）が正式GAとなり、P-054の「コーディング性能でOpus 4.8を+11pt超え」の前提がSWE-Bench Pro 80.3%（vs Opus 4.8: 69.2%）で実証された。ただし6月9日リリース直後に発覚した「フロンティアLLM開発に関する要求を不可視で劣化させるセーフガード」問題は、企業ユーザーの信頼性懸念として残っている（Anthropicは「誤ったトレードオフ」として可視化方針に変更）。また旧ゼロリテンション契約ユーザーへの30日データ保持義務化は未解決の可能性がある。エンタープライズ用途では使用するモデルと使用目的の組み合わせを明示記録することでコンプライアンスリスクを管理。

**提案アクション**:
1. sandbox/FX自動取引/config.py の `PREMIUM_MODEL` を `claude-fable-5-20260609` に更新し、同一バックテストタスクでOpus 4.8対比の精度とコストを計測
2. CLAUDE.mdに「Fable 5を使用するタスク一覧：コーディング・リファクタリング・バグ修正。使用しないタスク：生物学・フロンティアAI研究関連（過剰制限が発生する可能性）」を明記
3. 旧ゼロリテンション契約（エンタープライズ）の場合、30日データ保持ポリシー変更の適用状況を確認し、機密データをFable 5に送信する前に法務確認を実施

---

### P-065: Claude Code 5段階ネストサブエージェントを日次収集エージェントに適用

**根拠記事**: 236 (Claude Code 2026年6月大型アップデート), 243 (5段階ネストサブエージェント ofox.ai)
**詳細**: v2.1.172（2026年6月10日）で最大5段階のネストサブエージェントが解禁された。現在の日次収集エージェントは4ドメイン並列（P-023）だが、ネスト機能を使うことで「ドメイン別オーケストレーター（Layer 1）→各クエリ実行エージェント（Layer 2）→記事品質チェック（Layer 3）」の3層構成が可能になる。推奨深さは2〜3段階（ofox.ai）であり、過深ネストによるコスト指数増大に注意。モデルは外側（Layer 1）にOpus/Fable 5、内側（Layer 2-3）にSonnet/Haikuを割り当てることでコスト最適化できる。

**提案アクション**:
1. P-023の4ドメイン並列Subagent YAML定義を「Layer 1: ドメインオーケストレーター × 4、Layer 2: クエリ実行エージェント × n」の2層構成に拡張
2. 各LayerのモデルをCLAUDE_CODE_SUBAGENT_MODEL環境変数でLayer別に設定（Layer 1: claude-opus-4-8、Layer 2: claude-haiku-4-5で約60%コスト削減）
3. 3段階以上にネストする前に必ずトークン計算を行い、コスト上限を設定してから実装（`max_tokens: 5000` 等のガードを各エージェントに追加）

---

### P-066: Claude Code Safe Modeをデバッグ標準手順としてCLAUDE.mdに追加

**根拠記事**: 241 (Claude Code Safe Mode & フォールバックチェーン 実践ガイド)
**詳細**: 2026年6月追加の `--safe-mode`（または `CLAUDE_CODE_SAFE_MODE=1`）フラグはCLAUDE.md/プラグイン/スキル/フック/MCPを全無効化してクリーンな状態でデバッグするための公式トラブルシュートツール。bpr_labで多数のスキル・フック・MCP（P-011・P-013・P-023参照）が複雑に絡み合う構成になるにつれ、Safe Modeによる問題切り分けが必須になる。現在CLAUDE.mdにこの手順が未記録であり、問題発生時の対応が属人化している。

**提案アクション**:
1. CLAUDE.mdの「トラブルシュート」セクションに「Safe Mode起動: `claude --safe-mode` または `export CLAUDE_CODE_SAFE_MODE=1`。全カスタマイズ無効で素のClaudeで問題が再現するか確認する」を追記
2. フォールバックモデルチェーンの設定例（Fable 5 → Opus 4.8 → Sonnet 4.6）を `.claude/settings.json` の雛形としてリポジトリに追加
3. P-056（FX自動取引パイプラインへのフォールバック組み込み）と統合して設定ファイルを一元管理

---

### P-067: 米国AI規制環境の重大変化 — GAAIA + Colorado法差し替えでコンプライアンス戦略を再設計

**根拠記事**: 238 (Colorado AI Act廃止 Norton Rose), 239 (GAAIA DLA Piper), 240 (GAAIA vs 州法 FPF)
**詳細**: P-035・P-049・P-055のコンプライアンス前提が再び変化。確定事実: (1) Colorado SB 26-189成立（5/14署名、2027/1/1施行）で旧法のリスク管理・年次評価義務がなくなり「通知と透明性」のみに縮小、(2) 連邦地裁がxAI申請で旧Colorado法の執行を仮差し止め、(3) GAAIA草案（6/4）は3年プリエンプション条項含み成立すれば州法（SB26-189も）が凍結される可能性。実務的結論: 2027年1月まで余裕があり、連邦法の行方が不確実なため「HITL実装（P-025）の優先継続」と「法的動向の季報チェック」のみで対応。

**提案アクション**:
1. P-035・P-049の「Colorado対応優先」ステータスを「待機中：SB 26-189施行2027年1月、GAAIA成立見込み未確定」に更新
2. CLAUDE.mdに最新ステータスを反映：「AI規制適用状況（2026年6月時点）: Colorado SB 26-189は2027年1月施行予定、GAAIA成立すれば3年プリエンプション。直近はHITL（P-025）優先で対応」
3. 次回規制チェックポイントを2026年9月末（GAAIA草案への議会フィードバック期限後）に設定

---

### P-068: MCP OAuth 2.1必須化への移行計画 — 新規実装を今からRC仕様準拠に

**根拠記事**: 244 (MCP OAuth2エンタープライズ認証ロードマップ callsphere), 223 (MCP RC公式発表)
**詳細**: P-017・P-041・P-061で提案してきたMCPステートレス化への対応として、OAuth 2.1必須化の具体的なタイムラインが確定した。MCPサーバーはOAuth 2.1 Resource Serverとして公式分類され、APIキー認証はエンタープライズユースケースで非推奨になる。P-011（FXバックテストMCPサーバー）・P-013（MetaTrader MCPサーバー）の新規実装は今からOAuth 2.1で設計を開始することで、2026年7月28日の最終仕様公開後の改修コストをゼロにできる。

**提案アクション**:
1. P-011（FXバックテストMCPサーバー）の認証設計をOAuth 2.1 Resource Serverパターンで設計（シンプルな実装: Authorization Server = ローカルKeycloak or Auth0無料Tier）
2. P-013（MetaTrader MCPサーバー）はgitHub: ariadng/metatrader-mcp-serverのIssue/PRで2026-07-28仕様対応状況を確認し、対応済みなら採用・未対応なら自前でOAuth 2.1ラッパーを追加
3. CLAUDE.mdの「MCPサーバー開発ガイドライン」セクションに「認証: OAuth 2.1 Resource Serverパターン必須（APIキー認証は非推奨）」を追記（P-041の更新版）

---

## 2026-06-13 提案

### P-069: EU AI Act 8月2日完全施行への具体的対応チェックリスト作成

**根拠記事**: 274 (ChatGPT生成AI規制状況 2026年6月JA), 267 (P-067補完)
**詳細**: 2026年8月2日にEU AI Actが完全施行される（残り50日）。P-067でGAAIA/Colorado対応を「待機中」としたが、EU AI Actは8月2日に確定施行。bpr_labのFX自動取引ボットがEU居住者に向けたサービスの場合（またはEUデータを処理する場合）、ハイリスクAIシステム（信用スコアリング類似の金融意思決定）として登録義務が生じる可能性がある。日本市場のみを対象とする場合でも、AnthropicのAPIサーバーがEU内にある場合はデータ処理者として影響を受ける可能性がある。今月中の対応確認が必要。

**提案アクション**:
1. sandbox/FX自動取引/のターゲット市場（日本のみか、EU向けも含むか）を確認し、EU AI Actの適用可能性を法務的にチェック
2. 適用対象の場合：「自動化された意思決定システム」としてAnnex IIIリスト（信用・保険・雇用・法執行等）への該当有無を確認
3. CLAUDE.mdに「EU AI Act（2026年8月2日完全施行）: FX自動取引が日本市場のみ向けであれば直接適用外と解釈するが、EU処理データが含まれる場合は要確認」を注記
4. 次回確認タイミング: 2026年7月15日（施行2週間前）

---

### P-070: SIOS Tech Lab 無償SKILL.mdテンプレートを bpr_lab スキル整備の出発点に活用

**根拠記事**: 264 (Claude Code Skills 汎用テンプレート公開 SIOS Tech Lab JA)
**詳細**: SIOS Tech Labがコードレビュー・テスト生成・ドキュメント作成・リファクタリングの4種類のSKILL.mdテンプレートを無償公開した。P-039（bpr_lab スキル体系再整理）・P-060（SKILL.md description最適化）を具体化するための出発点として活用できる。特にコードレビュースキルは `/code-review` の代替として、FX自動取引コードの品質確認（P-031 ultrareviewの補完）に使える。テンプレートのdescriptionフィールドが自然言語で具体的に記述されており、P-060の「自動トリガー精度改善」の参考にもなる。

**提案アクション**:
1. SIOS Tech Lab公開のSKILL.mdテンプレート（4種）を `.claude/skills/` の雛形として取り込む（`git clone` またはコピー）
2. 各テンプレートのdescriptionを bpr_lab固有のユースケース（「FX自動取引コードのレビュー」「CLAUDE.md整備チェック」等）に書き換え、P-060のdescription最適化と同時に実施
3. 新規スキルの追加優先順位: `/fx-review`（P-037）→ `/catalog-update`（P-003）→ `/daily-collect`（P-003）の順でテンプレートから実装

---

### P-071: Fomoed AI取引プロンプト集のMT5接続テンプレートを sandbox/FX自動取引/ に適用

**根拠記事**: 271 (15 AI Trading Bot Prompts No Coding 2026 Fomoed), 272 (MT5+ChatGPT完全ガイド MQL5)
**詳細**: Fomoed の15プロンプト集はMT5・Interactive Brokers・Alpaca API用の接続コード例付きで、P-030（FastAPIアーキテクチャ適用）の実装加速に直接使用できる。MQL5 blogの4層アーキテクチャ実装記事（P-014と同等の信頼度閾値設計）と組み合わせると、sandbox/FX自動取引/のプロトタイプを即日構築できる。特に「バックテスト用プロンプト」と「MT5デモ口座接続コード」の部分はP-030のアクション3（MT5デモ口座でのPaperトレードモード確認）に対応する。

**提案アクション**:
1. Fomoed の「トレンドフォロー」「平均回帰」「リスク管理」プロンプトをsandbox/FX自動取引/prompts/ ディレクトリに保存（テンプレートとして管理）
2. P-014の信頼度閾値（0.55/0.75）を各プロンプトのリスク管理セクションに明示的に組み込む形にカスタマイズ
3. MQL5 blogの信頼度閾値実装（Claude API呼び出し時のconfidence field要求）をP-030のserver.py実装に取り込み、P-025（HITL）との統合を完成させる
4. MT5デモ口座環境が整っている場合は今週中にFomoed テンプレートのバックテスト用プロンプトを試験実行し、結果をP-026（乖離分析）のベースラインデータとして記録
---

## 2026-06-14 提案

### P-072: Fable 5 全世界停止に伴うモデル選択戦略の緊急見直し — P-054・P-064を一時中断

**根拠記事**: 275 (Anthropic公式声明 Fable 5/Mythos 5停止), 276 (The New Stack 停止命令), 277 (Trump政権対立), 278 (White House協議)
**緊急度**: 高（6/14時点でFable 5グローバル停止中）
**詳細**: 2026年6月12-14日、米政府指令によりClaude Fable 5（claude-fable-5-20260609）とMythos 5が全世界でアクセス不能になった。P-054（Fable 5モデル採用検討）・P-064（Fable 5本番採用）の実装計画を一時中断し、Opus 4.8（claude-opus-4-8）を最高性能モデルとして使用し続けるフォールバック体制に戻す必要がある。ホワイトハウス協議（来週予定）の結果次第で: (a)再開（条件付き）、(b)米国人ユーザー限定、(c)長期停止 の3シナリオがある。P-056（fallbackModel設定）のフォールバックチェーンから Fable 5 を一時除外し、最高性能レイヤーをOpus 4.8に戻す。

**提案アクション**:
1. sandbox/FX自動取引/config.py の `PREMIUM_MODEL` を `claude-opus-4-8` に戻す（Fable 5停止対応）
2. `.claude/settings.json` の `fallbackModel` 設定からFable 5を除外し `claude-opus-4-8` → `claude-sonnet-4-6` → `claude-haiku-4-5` に変更
3. CLAUDE.mdに「⚠️ Claude Fable 5は2026年6月12日〜米政府指令により停止中。次回確認: ホワイトハウス協議結果（6月第3週目安）」を追記
4. ホワイトハウス協議結果を受け、再開後にP-054・P-064の実装を再開するトリガーとして PROPOSALS.md に記録

---

### P-073: QuantaAlphaの進化的αファクターマイニングをFX自動取引の戦略開発に適用

**根拠記事**: 285 (QuantaAlpha arxiv:2602.07085 清華大・北大)
**詳細**: QuantaAlpha（清華大・北大・CAS・CMU・HKUST、2026年2月）はLLMエージェントによるαファクター自動マイニングを「軌跡（trajectory）レベルの進化的最適化」で大幅改善した論文。既存手法（RD-Agent・AlphaAgent）対比でIC +0.0535〜+0.0970、ARR +12〜18%の改善を実証。CSI 300で学習した因子がS&P 500へ転用可能（累積超過リターン137%）。P-004（TradingAgentsアーキテクチャ）とP-033（TradingAgents + Claude 4.x）の「シグナル生成」レイヤーに、QuantaAlphaの進化的最適化アプローチを組み込むことでシステマティックなαファクター探索が可能になる。GitHub公開済みで実装コードが入手可能。

**提案アクション**:
1. QuantaAlphaのGitHub（github.com/QuantaAlpha/QuantaAlpha）をクローンし、EUR/USDのFXデータでの動作確認を試験実施
2. P-014（信頼度閾値）のconfidence値を、QuantaAlphaが出力するIC（情報係数）とARR（年間リターン率）から動的に計算するアダプターを設計
3. P-043（LLMバージョン固定・再現性確保）の原則をQuantaAlpha実行時にも適用: 使用モデル・日付・データソースを記録してタスクの再現性を保証
4. CSI 300→S&P 500のファクター転用実績を参考に、FXペア間（EUR/USD→USD/JPY）のファクター転用可能性を検証

---

### P-074: Colorado AI Act 6月30日施行 (残16日) — P-067の待機方針から最終確認へ

**根拠記事**: 281 (AIガバナンス主導権争い Vorys分析), 277 (Trump政権AIモデル規制)
**詳細**: P-067で「Colorado SB 26-189は2027年1月施行で余裕あり」と判断したが、Vorys法律事務所の最新分析（2026年6月14日）でColorado旧法（SB24-205）の6月30日施行に向けた最終確認が必要と指摘されている。旧法と新法（SB 26-189）の移行スケジュールの解釈が複雑なため、bpr_labのFX自動取引ボットが「自動化された意思決定ツール（ADMT）」として旧法の適用対象になる期間（6月30日〜12月31日）がある可能性がある。White House vs 州法の対立（Fable 5停止事例含む）により、連邦AI規制の影響範囲が拡大する傾向を踏まえ、早めの確認を推奨。

**提案アクション**:
1. Colorado旧法（SB24-205）の6月30日施行と新法（SB 26-189）の2027年1月施行の重複期間（7月〜12月）でのADMT義務を法務確認（P-035のアクション1を6月30日前に完了）
2. Vorys分析のWhite House プリエンプションシナリオ（6/2大統領令）がColorado法を事実上無効化している場合は対応不要と判断できる旨をCLAUDE.mdに注記
3. 次回確認タイミング: 2026年7月1日（Colorado法施行翌日）に確認し、GAAIA動向と合わせて評価（P-049との統合）

---

## 2026-06-16 提案

### P-075: P-006/P-012 緊急対応を「待機」に格下げ — Agent SDK課金変更が一時停止中

**根拠記事**: 289 (Anthropic Pauses Agent SDK Credit Split - Digital Applied), 288 (Claude Code Pricing June 2026 - Bind AI)
**詳細**: P-006（緊急度高）およびP-012で対応を促していた2026年6月15日のAgent SDK課金分離変更が、AnthropicによりLast Minuteで一時停止された。現時点では非インタラクティブ実行のクレジット分離は**未施行**。施行時期は未定。sandbox/FX自動取引/のコスト試算や、日次収集エージェントのコスト見直しは再開通知まで待機。ただしP-012のモデルIDリタイア（claude-sonnet-4-20250514等）はAgent SDK課金と無関係のため引き続き対応必要。

**提案アクション**:
1. P-006・P-007（Agent SDK課金変更関連）の緊急フラグを一時解除し、Anthropicの再施行アナウンスを待つ
2. P-012のモデルIDリタイア確認（`grep -r "sonnet-4-20250514\|opus-4-20250514" .`）は引き続き実施
3. Anthropicの公式ブログ・Releasebot（releasebot.io/updates/anthropic）を週次チェックし、再施行アナウンスに備える
4. 再施行時には最新の料金表（288 Bind AI記事）を基に月次コスト試算を即時更新

---

### P-076: v2.1.178 新パーミッション構文を settings.json に適用

**根拠記事**: 286 (Claude Code v2.1.178 DevelopersIO JA)
**詳細**: 2026年6月16日公開のv2.1.178でパーミッションルールの新構文が導入された。ネストした `.claude` ディレクトリのサポートも強化されており、プロジェクト配下のサブディレクトリ（sandbox/FX自動取引/等）に独立した `.claude/settings.json` を配置してスコープ別に権限を細分化できる。`enforceAvailableModels` によるモデルアローリスト管理も利用可能に。FX自動取引ディレクトリのように実資金に触れるコードは、専用の `.claude/settings.json` で権限を絞ることが推奨される。

**提案アクション**:
1. `sandbox/FX自動取引/.claude/settings.json` を新規作成し、FX取引専用の権限セット（読み取り・MT5 API呼び出し限定・本番APIへの直接書き込み禁止）を新構文で記述
2. `enforceAvailableModels` を設定し、FX取引サブエージェントが利用可能なモデルをOpus 4.8・Sonnet 4.6のみに制限
3. ネストした `.claude` サポートを利用して、bpr_lab全体の `.claude/settings.json`（グローバル）とFX固有の設定を階層管理

---

### P-077: LLM金融戦略の長期アウトパフォーム困難の実証 — FX自動取引の設計原則見直し

**根拠記事**: 290 (arxiv 2505.07078 LLM Financial Strategies Cannot Outperform Market Long Run)
**詳細**: 2505.07078論文が20年間・100銘柄超で実証した「LLMアルファの長期劣化」と「ブル相場過保守・ベア相場過攻撃」の非対称性は、bpr_labのFX自動取引設計における重要な制約。P-020（TrustTrade式コンセンサス）・P-033（TradingAgents + Claude 4.x）を推進する際、「LLMをメインシグナルにする設計」の限界を認識した上で実装すべき。P-026（3ヶ月実験の教訓）で既に「補助役割として使うべき」と結論付けていたが、本論文がその学術的根拠を提供した。特にFXはバックテスト→実取引ギャップがさらに大きいため（高頻度・スリッページ・スワップ）、LLMはシグナル「候補生成」に留め最終執行はルールベースに委ねる原則を強化すべき。

**提案アクション**:
1. sandbox/FX自動取引/architecture.md に「LLM役割: 非構造化データ解析・シグナル候補生成のみ。最終エントリー判断・リスク管理はルールベース」と明記
2. P-014（信頼度閾値）のconfidence閾値を「LLMシグナルの直接採用閾値」ではなく「ルールベースフィルタへの入力スコア」に再定義
3. バックテスト評価指標に「ブル相場パフォーマンス」「ベア相場パフォーマンス」を必ず分離追加し、非対称リスクを可視化

---

### P-078: AY Automate 15フックサンプルからコスト監視フックを即採用

**根拠記事**: 297 (15 Best Claude Code Hooks Copy-Paste Ready 2026 - AY Automate)
**詳細**: AY Automateが公開した15種のCopy-Paste対応フックサンプルのうち、bpr_labの日次収集エージェントに即採用できるものが複数ある。特に「コスト監視フック（Stop時の累積トークン・コスト集計）」は、P-075（Agent SDK課金変更の再施行モニタリング）と組み合わせて実際のコストを可視化する手段として有効。「セッション終了時のgit commit自動化フック」はStep 5（コミット&Push）の手動作業を削減できる。P-038（自己学習型フック）と組み合わせることで、コスト監視＋知識蓄積の自動パイプラインを構築できる。

**提案アクション**:
1. AY Automateのコスト監視フック（Stop/SubagentStop フックで累積トークン・概算コストをJSONログに出力）を `.claude/settings.json` に追加
2. セッション終了時のgit commit自動化フック（Stopフック: 変更があれば `git add -A && git commit -m "auto: セッション自動コミット"` を実行）を試験導入
3. 上記2フックを1週間運用し、日次収集エージェントの実際のトークン消費量・コストを記録してP-075の再施行時コスト試算の実データとして活用

---

## 2026-06-17 提案

### P-079: SKILL.md frontmatterへのHooks直書き技法を bpr_lab スキルに導入

**根拠記事**: 309 (Qiita Tips: HooksをSKILL.mdに直書き)
**詳細**: SKILL.mdのfrontmatter（`---`ブロック）にhooksキーを追加するだけで、settings.jsonと等価のHooks設定が機能することが確認された。bpr_labの.claude/skills/配下の各スキルが独自のPostToolUse/PreToolUse hookを必要とする場合（例：日次収集スキルが終了後に自動コミットするhook）、settings.json一元管理から「スキルとフックのひとつのファイル管理」に移行することで保守性が大幅に向上する。P-038（自己学習型フック）・P-078（コスト監視フック）の実装もSKILL.md内に統合できる。

**提案アクション**:
1. `.claude/skills/`配下の各SKILL.mdのfrontmatterに対応するhooks定義を移植し、settings.jsonのhooksセクションをスリム化
2. `.claude/skills/daily-collect/SKILL.md`（P-003）に「Stop後に git add・commit・push を実行するhook」を frontmatterで直書きし、Step 5の手動コミット作業を自動化
3. チームリポジトリに共有する場合は.claude/skills/ディレクトリをGitに含めることで、hooks定義も同時に共有可能になる利点をCLAUDE.mdに記録

---

### P-080: FX自動取引ボットの「7コンポーネント完成度監査」を実施

**根拠記事**: 314 (MQL5ブログ: AIトレーディングの7コンポーネント), 312 (LLM比較: Pythonアルゴ取引ボット生成)
**詳細**: MQL5コミュニティの実証記事が「完全なAI取引システムには7コンポーネントが必要」と定義した（①LLMモデル選択、②システムプロンプト設計、③コンテキストフォーマット、④呼び出し頻度最適化、⑤リスク管理レイヤー、⑥バックテスト統合、⑦モニタリング・ロギング）。現在のsandbox/FX自動取引/がこの7コンポーネントのうちどこまで実装済みかを棚卸しすることで、優先実装項目が明確になる。また、LLM比較実験（記事312）でClaude Opus 4.7が「確認ロジックが堅牢で保守的」と評価されており、リスク管理重視のFXボットに適したモデルであることが改めて確認された。

**提案アクション**:
1. `sandbox/FX自動取引/architecture.md` に7コンポーネントのチェックリストを作成し、各コンポーネントの実装状態（未着手/進行中/完了）を記録
2. 最優先未実装コンポーネントを特定し、次のスプリントのタスクとして登録（特に⑤リスク管理レイヤーの「LLMの外側への配置」が最重要）
3. P-014（信頼度閾値）・P-025（HITL設計）・P-043（LLMバージョン固定）を7コンポーネントフレームワークに対応付けて、既存提案の優先順位を整理

---

### P-081: EU AI法 HRAI期限延期（2026/8→2027/12）による規制対応優先度の見直し

**根拠記事**: 316 (EU AI法 Digital Omnibus改正: HRAI期限延期)
**詳細**: 2026年5月7日の暫定合意でAnnex III高リスクAI（HRAI）義務が1.5年延期（2026年8月→2027年12月）された。P-049（Colorado法監視）・P-055（GAAIA草案対応）・P-035（FX自動取引のADMT適用確認）との関係を再整理する必要がある。EU法上の義務延期は日本・米国の規制に直接影響しないが、グローバルAIガバナンスの趨勢として「高リスクAI義務の段階的施行」が主流になっており、P-025（HITL設計）・P-077（LLM役割限定）の方向性が国際的なスタンダードと整合していることを確認できた。なお、汎用AI（GPAI）モデル義務（Anthropic等の開発者に課される義務）は8月2日施行のまま変更なし。

**提案アクション**:
1. `sandbox/FX自動取引/README.md` の規制対応注記を更新：「EU AI法 Annex III HRAI義務は2027年12月まで延期。GPAIモデル義務（Anthropic側）は2026年8月施行。本システムは利用者として直接対象外だが、利用するAPIプロバイダーの規制準拠状況を定期確認」
2. P-025（HITL設計）・P-077（LLM役割限定）を「EU AI法・Colorado法・日本AIガイドラインに共通する推奨設計原則」として位置付け直し、単一の法律対応ではなく普遍的なベストプラクティスとして実装
3. 次回規制監視タイミングを「2026年8月1日（EU GPAI義務施行直前）」と「2026年7月末（EU Digital Omnibus正式採択後）」の2点に設定

---

## 2026-06-18 提案

### P-082: Fable 5/Mythos 5シャットダウン（90分通知）を踏まえたAI依存リスク管理戦略の策定

**根拠記事**: 325 (Claude Updates May–June 2026: Opus 4.8, SpaceX, Managed Agents), X#SIGNAL claude-ecosystem (@HaraKazuo, @c64f7e94, @AISTATSCH 他)
**詳細**: 2026年6月、米国政府の指示によりAnthropicがFable 5（Mythos 5）の国外アクセスを90分前通知で停止した事例が発生。bpr_labはClaude APIに全面依存しているため、モデル突然失効・国外制限・ITAR/EAR輸出規制による停止リスクが現実的脅威として顕在化した。DoD（米国防省）もAnthropicから契約の2/3以上をOpenAI・Google・Metaに移行したとされ、政府との関係が企業の安定性リスクに直結する。個人・スタートアップ規模でも「主力モデルへのシングルポイント依存」は業務継続リスクである。

**提案アクション**:
1. `CLAUDE.md`（またはプロジェクトルート）に「AIモデル依存リスク管理ノート」を追加：現在使用中のモデルID、代替モデル（OpenAI GPT-5.5、Google Gemini 3.x）へのフォールバック手順、APIキー切り替え方法を文書化
2. 日次収集エージェント（bpr_lab）が使用するモデルを設定ファイル（`.env`または`CLAUDE.md`）で管理し、モデルIDをハードコードしない設計に移行
3. 月1回「モデルアクセス状況確認」タスクをスケジュール：使用中Anthropicモデルの提供状況・輸出規制対象指定有無を確認

---

### P-083: NVIDIA SkillSpector（64脆弱性クラス検査）でbpr_labのClaudeスキルをセキュリティ監査

**根拠記事**: X#SIGNAL claude-code (@VivekIntel: NVIDIA SkillSpector announcement)
**詳細**: NVIDIAがSkillSpectorというClaude Code Skills向けセキュリティスキャンツールをリリース。64種の脆弱性クラスを検出し、コード生成・実行時のインジェクション・権限昇格・機密情報漏洩リスクを特定する。bpr_labの`.claude/skills/`配下には日次収集・Python実行・ファイル書き込みを行うスキルが存在し、外部入力（Webサーチ結果、Xポスト）を処理するため、プロンプトインジェクション対策の確認が重要。

**提案アクション**:
1. SkillSpector（NVIDIAのGitHubまたはClaudeマーケットプレイスで公開予定）のインストール手順を確認し、`.claude/skills/`配下の全SKILLに対して実行
2. 検出された脆弱性のうち「高リスク」分類を優先修正（特に外部入力のサニタイズ不足、過剰な権限付与）
3. 月次セキュリティ監査タスクとしてSkillSpector実行をbpr_labの運用ルーティンに追加

---

### P-084: ZenomTrader方式のClaude×MT5自律バックテスト統合をFXプロジェクトに実装

**根拠記事**: X#SIGNAL ai-trading (@ZenomTrader: Claude autonomous MT5 backtesting tool)
**詳細**: ZenomTraderが「Claudeがデータ分析→戦略立案→MT5内でのバックテスト実行→結果評価→戦略修正」の全サイクルを自律的に完結させるツールを公開（Claude Code + MT5 Terminal MCP連携）。現在のsandbox/FX自動取引/ではバックテストは手動実行だが、このアーキテクチャを採用すれば「バックテストのループ高速化」と「P-080（7コンポーネント）の⑥バックテスト統合」が同時に達成できる。MT5 MCPサーバー（MetaTrader-MCP, 記事057）がすでにライブラリに存在しており、技術的な土台はある。

**提案アクション**:
1. ZenomTraderのツール（GitHubリポジトリ）を確認し、MT5 MCP連携のアーキテクチャをsandbox/FX自動取引/design.mdに転記・分析
2. 最小実装として「Claudeに戦略パラメータを渡す→MT5でバックテスト実行→結果をJSON返却→Claudeが評価」の1サイクルをPython/MCPで実装
3. P-080（7コンポーネント）の⑥バックテスト統合と組み合わせ、ZenomTrader方式を採用した場合のアーキテクチャ図を作成

---

### P-085: CoinbaseのSEC登録AI投資顧問（業界初）を踏まえたAI売買エージェントの法的要件調査

**根拠記事**: X#SIGNAL ai-trading (@Tawney_jjones, @CryptoJPTrans: Coinbase AI investment advisor SEC registration), ai-news (@IROHANI_shotime)
**詳細**: CoinbaseがAIエージェントをSEC（米証券取引委員会）に投資顧問として登録（業界初）。自律的に資産運用できる法的根拠を持つAIエージェントが登場したことで、AI自動取引エージェントの規制フレームワークが現実化した。日本ではFX自動売買は登録業者が提供するEA（Expert Advisor）として扱われるため、個人が「AIが自律的に売買判断するシステム」を開発・運用する場合の法的地位を改めて確認する必要がある。P-025（HITL設計）・P-077（LLM役割限定）の「最終判断は人間が行う」設計原則の法的根拠としてこの事例を活用できる。

**提案アクション**:
1. 日本の金融商品取引法における「自動取引システムの個人運用」の現行規制（2026年版）を調査し、sandbox/FX自動取引/legal-notes.mdに要点をまとめる
2. P-025（HITL設計）の設計根拠に「SEC登録AI投資顧問事例により自律型AIの法的承認が進展中だが、日本ではHITL原則が安全側」を追記
3. Coinbaseの事例を「AI自動取引の国際規制動向ウォッチ」として月次収集テーマに追加

---

### P-086: Anthropic 400kセッション研究の主要知見をbpr_lab日次収集エージェント設計に反映

**根拠記事**: X#SIGNAL claude-code (@6i8PTmb4OY50019, @tenobrus, @Kylechasse: Anthropic 400k session study findings)
**詳細**: Anthropicが40万件のClaude Codeセッションを分析した研究で、主要知見が明らかになった：①平均セッションは4ターンで完了（長期セッションは効率低下の傾向）、②ドメイン専門知識を持つユーザーは専門知識なしの5倍の成果を上げる、③専門性が高いほどAIとの協働品質が向上する。bpr_labの日次収集エージェントは長大なセッションになりがちで、コンテキスト圧縮・要約が頻発している。4ターン完了の原則に近づけるためにセッション構造を見直す価値がある。

**提案アクション**:
1. 日次収集エージェントの現在のターン数を記録（次回ルーティン実行時にカウント）し、平均値が研究知見（4ターン）の何倍かを測定
2. 収集/分類/カタログ更新/コミットの4フェーズを「各フェーズ独立セッション」として分割実行する設計案を検討（現在は1セッションで全フェーズを実行）
3. 「ドメイン専門性が成果を5倍にする」知見を踏まえ、日次収集のクエリ設計を更にドメイン特化させるためのクエリリスト改訂（特にai-trading分野のMT4/MT5固有クエリ強化）
