# リモート開発コントロール

## プロジェクト概要

- **目的**: ConoHa Windows VPS 上に OpenClaw を構築し、Telegram から Claude Code と自由に会話できるリモート開発環境を整備する
- **対象**: 自分（タクミ）— スマホから開発タスクの投入・進捗確認・ログ閲覧を行いたい
- **主要な価値**: 外出中・移動中でもPCの開発環境をフル活用でき、FX自動取引等の既存PJもリモート監視・操作できる

## 調査の問い

| # | 問い | 出力ドキュメント | 依存 | 手法 |
|---|------|-----------------|------|------|
| Q1 | OpenClaw のアーキテクチャ・セットアップ手順（Windows対応状況、Telegram連携設定） | docs/01_openclaw.md | なし | evidence_collection |
| Q2 | ConoHa Windows Server のスペック・料金・MT5/Claude Code同居可能性 | docs/02_conoha_vps.md | なし | evidence_collection |
| Q3 | セキュリティ構成（Tailscale vs Cloudflare Tunnel vs SSH tunnel、VPS hardening） | docs/03_security.md | Q1, Q2 | critical_verification |
| Q4 | 統合 — 推奨構成と構築手順書の作成 | docs/04_setup_guide.md | Q1〜Q3 | synthesis |

## ディレクトリ構造

    リモート開発コントロール/
    ├── docs/             # 調査ドキュメント（主成果物）
    ├── references/       # 元資料・参考文献の格納
    ├── .claude/
    │   ├── claude.md       # このファイル
    │   ├── settings.json   # WebSearch/WebFetch自動承認フック
    │   ├── whiteboard.md   # エージェント間情報共有（追記のみ）
    │   └── agents/         # エージェント定義
    ├── PLANS.md          # 進捗・意思決定の記録
    ├── .env.example      # 環境変数テンプレート
    └── .gitignore

## エージェント共通ルール

- `.claude/whiteboard.md` はエージェント間の情報共有ファイル（Subagent・Agent Teams 共通）
- Agent Teams テームメイトは whiteboard.md のステータステーブルを必ず更新すること
- 詳細はエージェント定義の「Whiteboard」セクションを参照

## 調査ルール

### ソースと信頼性

- **全ての主張にソース（URL・出典）を必ず付ける**
- 一次ソース（公式ドキュメント・GitHubリポジトリ・公式ブログ）を優先する
- 同じ情報を異なるソースでクロスチェックする
- 情報の鮮度（年度）に注意し、古いデータには明示する
- OpenClaw/ClawPhone の公式GitHub リポジトリを最優先ソースとする
- ConoHa の公式料金ページ・スペックページを参照する

### 分析姿勢

- 主張を無批判に受け入れない（批判的検証を徹底する）
- 具体的な数字・データを優先する（定性的な印象より定量的な根拠）
- 反例や不利なデータも公平に扱う
- セキュリティに関する主張は特に厳格に検証する

### 品質チェック

- 各ドキュメントは fact-checker で事実検証を実施
- 統合ドキュメントは devils-advocate で論理攻撃を実施
- fact-checker → 修正反映 → devils-advocate の順序を守る（並列不可）

## サブエージェントのWebSearch権限

`.claude/settings.json` の2層構成でWebSearch/WebFetchを自動承認する:

1. **`permissions.allow`**（静的許可）: バックグラウンドサブエージェント起動前の事前承認ステージで評価される
2. **`PreToolUse` フック**（動的許可）: ツール使用時に評価されるバックアップ

## レビューワークフロー

    Phase 1: researcher (Q1, Q2 並列OK) → 各doc作成 → whiteboard.md に発見サマリーを追記
    Phase 2: researcher (Q3, Q4 逐次) → Q1,Q2の結果を踏まえて調査
    Phase 3: fact-checker → 事実修正を各docに反映
    Phase 4: devils-advocate → 論理攻撃 → 設計修正を反映

**whiteboard.md**: `.claude/whiteboard.md` はエージェント間の情報共有ファイル。各エージェントが作業開始時に読み、完了時にサマリーを追記する。追記のみ（削除・上書き禁止）。

## Agent Teams 運用（3+ 並列実行時）

Agent Teams でテームメイトとして起動された場合、以下のルールに従う。

### テームメイトの義務

1. **作業開始時**: `.claude/whiteboard.md` を読み、ステータステーブルに自分の行を追加する
2. **各タスク完了時**: ステータステーブルの自分の行を Edit で更新する（進捗カウントと最終更新時刻）
3. **作業完了時**: ステータステーブルの状態を `✅ 完了` に更新し、ログセクションにサマリーを追記する
4. **成果物は即時書き出し**: 全タスク完了を待たず、各タスク完了時に docs/ にファイルを書き出す

### チームリードの状態確認

- `.claude/whiteboard.md` の **ステータステーブル** を Read すれば全テームメイトの現在状態が分かる
- `.claude/team-activity.log` に TaskCompleted フックが活動ログを自動記録する

## 開発ルール

### コーディング規約
- コメントは日本語で書く
- 変数名・関数名は意味が明確な英語を使用
- 1関数は1つの責務に絞る

### Git規約
- コミットメッセージ: `<type>(<scope>): <subject>`
  - type: docs / fix / refactor
  - scope: doc名（01, 02等）
  - 日本語OK
- コミット前に動作確認を実施すること

### セキュリティ
- APIキー・シークレットは `.env` に格納し、`.gitignore` で除外
- ハードコードされた認証情報は絶対に禁止
- ユーザー入力は必ずバリデーション / サニタイズする

### エラーハンドリング
- 例外を握りつぶさない（空のexcept禁止）
- 外部API呼び出しにはタイムアウトとリトライを設定
- ユーザーに見せるエラーメッセージは日本語で分かりやすく

## 利用可能なエージェント

- `agents/researcher.md` — Web調査（バックグラウンド並列実行可能）
- `agents/fact-checker.md` — 事実検証（事実修正の直接適用可能）
- `agents/devils-advocate.md` — 反論・論理攻撃

<!-- 重要: 各エージェント定義の「起動方法」セクションに記載された subagent_type と mode を使うこと。
     Explore タイプでは Write/Edit が使えず、ファイル出力が空になる。
     全エージェントは subagent_type: general-purpose, mode: bypassPermissions で起動する。 -->

## プロジェクト固有のルール

- OpenClaw 公式ドキュメント（GitHub README・Wiki）を最優先ソースとする
- セキュリティ構成は「VPSをインターネットに直接公開しない」を原則とする
- VPS料金は月額ベースで比較し、年額割引は参考程度に留める
- 既存PJ（FX自動取引）との共存を常に考慮する（MT5のリソース消費等）
