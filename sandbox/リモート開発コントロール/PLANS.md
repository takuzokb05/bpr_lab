# リモート開発コントロール

<!-- このドキュメントは Living Document（生きた文書）である。
  作業の進捗、発見事項、設計判断をリアルタイムで更新し続けること。
  新しい Claude Code セッションでは、このファイルを最初に読み、
  現在地を把握してから作業を再開する。 -->

## Purpose / Big Picture

**完成物: Telegram → Claude Code リモート開発環境**

ConoHa Windows VPS 上に OpenClaw を構築し、スマホ（Telegram）から Claude Code と自由に会話できる環境を整備する。外出中・移動中でも開発タスクの投入・進捗確認・ログ閲覧が可能になる。

具体的には:
1. スマホの Telegram アプリからメッセージを送信する
2. VPS 上の OpenClaw が受信し、Claude Code を自律実行する
3. 結果を Telegram に返信する

**背景**: 現在のFX自動取引やその他の開発プロジェクトはローカルPC依存。外出中に状態確認やタスク投入ができず、生産性のボトルネックになっている。

## Progress

### Phase A: 調査 ← 現在のフェーズ

- [ ] Q1: OpenClaw のアーキテクチャ・セットアップ手順調査
- [ ] Q2: ConoHa Windows Server のスペック・料金・同居可能性調査
- [ ] Q3: セキュリティ構成の比較調査
- [ ] Q4: 統合 — 推奨構成と構築手順書の作成
- [ ] fact-checker による事実検証
- [ ] devils-advocate による論理攻撃

### Phase B: セットアップ実装

- [ ] VPS プロビジョニング（ConoHa Windows Server）
- [ ] OpenClaw インストール・設定
- [ ] Telegram Bot 設定・接続テスト
- [ ] 既存PJ（FX自動取引等）との連携設定
- [ ] セキュリティ設定（Tailscale等）
- [ ] 動作検証・ドキュメント整備

## Surprises & Discoveries

<!-- 作業中に遭遇した予期しない知見を記録する -->

## Decision Log

- 判断: アーキテクチャは OpenClaw ベースとする
  理由: 既存OSSを活用することで開発コストを最小化。Telegram連携が既に実装されている。
        カスタムTelegram Bot は自由度が高いが開発コストに見合わない。
  日付: 2026-03-03

- 判断: 実行環境は ConoHa Windows VPS とする
  理由: 24時間稼働が可能。MT5がWindows必須のため、Linux VPSは不可。
        既存ConoHa VPS（Linux 1GB）ではMT5非対応。
  日付: 2026-03-03

- 判断: ユースケースは自由会話型とする
  理由: 定型コマンド（Claude Codeタスク投入、MT5操作等）だけでなく、
        自然言語での自由な会話を重視。OpenClawのネイティブ機能として対応。
  日付: 2026-03-03

## Outcomes & Retrospective

<!-- 各Phase完了時に振り返りを記録する -->

## Context and Orientation

### ディレクトリ構造

    リモート開発コントロール/
    ├── PLANS.md              # このファイル
    ├── .claude/
    │   ├── claude.md         # Claude Code設定
    │   ├── settings.json     # 権限設定
    │   ├── whiteboard.md     # エージェント間情報共有
    │   └── agents/           # エージェント定義
    ├── docs/                 # 調査ドキュメント（主成果物）
    ├── references/           # 参考資料
    ├── .env.example          # 環境変数テンプレート
    └── .gitignore

### 用語定義

- **OpenClaw**: Claude Code をリモートから操作するためのOSSフレームワーク。Telegram bot 連携機能を持つ
- **ClawPhone**: Termux上でOpenClawを動かすための構成。スマホのブラウザからDashboardにアクセス可能
- **Tailscale**: WireGuardベースのVPN。セキュアなP2P接続を簡単に構築できる
- **ConoHa for Windows Server**: GMOのWindows VPSサービス。MT5の動作に必要

### 関連ファイル

- `.claude/claude.md`: プロジェクトのClaude Code設定
- `.env.example`: 環境変数の一覧
- `docs/`: 調査成果物

### 既知の制約

- MT5はWindows GUI常時起動が必要（ヘッドレス不可）
- ConoHa Windows Serverの最小プランのメモリ制限に注意（MT5 + Claude Code + OpenClaw の同居）
- OpenClawは比較的新しいOSSプロジェクトのため、ドキュメントや安定性に注意
