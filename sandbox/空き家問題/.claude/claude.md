# 空き家問題

<!-- base.md の内容を前提とする。以下は調査・分析プロジェクト固有の設定 -->

## プロジェクト概要

- **目的**: 横浜市における空き家問題の現状・課題・解決策を政策提言レベルで精査し、体系的なレポートとしてまとめる
- **対象**: 横浜市の空き家（特定空家等含む）、関連法制度、自治体施策
- **主要な価値**: データと事例に基づく実効性のある政策提言を導出する

## 調査の問い

| # | 問い | 出力ドキュメント | 依存 | 手法 |
|---|------|-----------------|------|------|
| Q1 | 横浜市の空き家の現状は？（戸数・空き家率・分布・増加傾向・全国比較） | docs/01_current_status.md | なし | evidence_collection |
| Q2 | 空き家問題の課題は何か？（所有者不明・老朽化・法制度の限界・地域影響・固定資産税特例） | docs/02_challenges.md | なし | root_cause_analysis |
| Q3 | 横浜市の既存施策とその効果は？（空家等対策計画・補助金・相談窓口・特定空家措置） | docs/03_yokohama_measures.md | なし | evidence_collection |
| Q4 | 他自治体・海外の成功事例は？（空き家バンク・リノベーション活用・ランドバンク等） | docs/04_case_studies.md | なし | critical_verification |
| -- | 統合分析・政策提言 | docs/05_policy_proposals.md | Q1〜Q4 | synthesis |

<!-- Q1〜Q4 は並列調査可能。Q5 は Q1〜Q4 完了後に analyst が実行 -->

## ディレクトリ構造

```
空き家問題/
├── docs/             # 調査ドキュメント（主成果物）
├── references/       # 元資料・参考文献の格納
├── .claude/
│   ├── claude.md       # このファイル
│   ├── settings.json   # WebSearch/WebFetch自動承認 + Agent Teams有効化
│   ├── whiteboard.md   # エージェント間情報共有（追記のみ）
│   └── agents/         # エージェント定義
│       ├── researcher.md
│       ├── analyst.md
│       ├── fact-checker.md
│       └── devils-advocate.md
└── PLANS.md          # 進捗・意思決定の記録
```

## 調査ルール

### ソースと信頼性

- **全ての主張にソース（URL・出典）を必ず付ける**
- 一次ソース（公式ドキュメント・学術論文・政府資料）を優先する
- 同じ情報を異なるソースでクロスチェックする
- 情報の鮮度（年度）に注意し、古いデータには明示する
- **優先ソース**: 総務省住宅・土地統計調査、国土交通省空き家対策資料、横浜市公式サイト、横浜市空家等対策計画
- **除外**: 不動産投資の営業記事、根拠なき楽観論

### 分析姿勢

- 主張を無批判に受け入れない（批判的検証を徹底する）
- 具体的な数字・データを優先する（定性的な印象より定量的な根拠）
- 反例や不利なデータも公平に扱う
- 政策提言は横浜市の財政規模・組織体制で実行可能かを常に検証する

### 品質チェック

- 各ドキュメントは fact-checker で事実検証を実施
- 統合ドキュメントは devils-advocate で論理攻撃を実施
- fact-checker → 修正反映 → devils-advocate の順序を守る（並列不可）

## サブエージェントのWebSearch権限

`.claude/settings.json` の2層構成でWebSearch/WebFetchを自動承認する:

1. **`permissions.allow`**（静的許可）: バックグラウンドサブエージェント起動前の事前承認ステージで評価される。これが最も確実な方法。
2. **`PreToolUse` フック**（動的許可）: ツール使用時に評価されるバックアップ。

この2層により、フォアグラウンド・バックグラウンド両方のサブエージェントでWebSearch/WebFetchが使える。

## レビューワークフロー

```
Phase 1: researcher (並列) → 各doc作成 → whiteboard.md に発見サマリーを追記
Phase 2: analyst → Q1〜Q4を統合 → docs/05_policy_proposals.md 作成
Phase 3a: fact-checker → 事実修正を各docに反映
Phase 3b: devils-advocate → 論理攻撃 → 修正を反映
```

**whiteboard.md**: `.claude/whiteboard.md` はエージェント間の情報共有ファイル。各エージェントが作業開始時に読み、完了時にサマリーを追記する。追記のみ（削除・上書き禁止）。

## Agent Teams 運用

Agent Teams でテームメイトとして起動された場合、以下のルールに従う。

### テームメイトの義務

1. **作業開始時**: `.claude/whiteboard.md` を読み、ステータステーブルに自分の行を追加する
2. **各タスク完了時**: ステータステーブルの自分の行を Edit で更新する（進捗カウントと最終更新時刻）
3. **作業完了時**: ステータステーブルの状態を `✅ 完了` に更新し、ログセクションにサマリーを追記する
4. **成果物は即時書き出し**: 全タスク完了を待たず、各タスク完了時に docs/ にファイルを書き出す

### チームリードの状態確認

- `.claude/whiteboard.md` の **ステータステーブル** を Read すれば全テームメイトの現在状態が分かる
- `.claude/team-activity.log` に TaskCompleted フックが活動ログを自動記録する

## Git規約

- コミットメッセージ: `<type>(<scope>): <subject>`
  - type: docs / fix / refactor
  - scope: doc名（01, 02等）
  - 日本語OK

## 利用可能なエージェント

- `agents/researcher.md` — Web調査（横浜市空き家ドメイン設定済み）
- `agents/analyst.md` — 統合分析（政策提言の評価軸設定済み）
- `agents/fact-checker.md` — 事実検証（自治体・住宅統計ドメイン設定済み）
- `agents/devils-advocate.md` — 反論・論理攻撃（政策提言の攻撃領域設定済み）

<!-- 重要: 各エージェント定義の「起動方法」セクションに記載された subagent_type と mode を使うこと。
     Explore タイプでは Write/Edit が使えず、ファイル出力が空になる。
     全エージェントは subagent_type: general-purpose, mode: bypassPermissions で起動する。 -->

## プロジェクト固有のルール

- 統計データは最新版（総務省 住宅・土地統計調査 2023年）を優先する
- 横浜市固有のデータと全国平均を常に比較する
- 政策提言は「横浜市の財政・組織で実行可能か」を必須検証項目とする
- 成功事例は人口規模・都市構造が横浜市と類似する都市を優先する
- 空家等対策の推進に関する特別措置法（2023年改正）の内容を正確に反映する
