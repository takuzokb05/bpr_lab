# PROPOSALS.md

収集記事を横断分析して得られた反映提案。
最終更新: 2026-05-28

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
