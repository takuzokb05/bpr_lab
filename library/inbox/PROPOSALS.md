# PROPOSALS.md

収集記事を横断分析して得られた反映提案。
最終更新: 2026-05-31

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
