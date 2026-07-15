# スライド作成ツール

## プロジェクト概要

- **目的**: ドキュメントから AI でスライドを自動生成する CLI ツール。NotebookLM の15枚制限を超え、枚数無制限・1枚単位リライト対応
- **対象ユーザー**: 自分用（プレゼン資料作成の効率化）
- **主要な価値**: 資料読込→テイスト設定→スライド生成→個別リライトの一気通貫フロー

## 技術スタック

- **言語**: Python 3.9+
- **フレームワーク**: CLI（argparse or click）
- **データベース**: なし
- **外部サービス**: Gemini API（ドキュメント解析・スライド構成）、Imagen 3（背景画像生成）、テキスト配置最適化AI（Phase A で選定）
- **パッケージ管理**: pip + requirements.txt

## フェーズ構成

このプロジェクトは hybrid 型（Phase A: 調査 → Phase B: 実装）で進行する。

### Phase A: 技術調査

| # | 問い | 出力 | 担当 | 依存 |
|---|------|------|------|------|
| Q1 | Gemini API のドキュメント解析能力とプロンプト設計 | docs/01_gemini_api.md | researcher | なし |
| Q2 | Imagen 3 の画像生成制約・出力形式・背景プロンプト手法 | docs/02_imagen3.md | researcher | なし |
| Q3 | python-pptx のレイアウト機能とテキスト配置の自由度 | docs/03_python_pptx.md | researcher | なし |
| Q4 | 各処理工程に最適な API モデルの比較選定 | docs/04_model_selection.md | analyst | Q1〜Q3 |

Q1〜Q3 は並列実行可能。Q4 は Q1〜Q3 完了後に実行。

### Phase B: 実装

Phase A の調査結果を踏まえて SPEC.md に機能一覧を具体化し、spec-driven-dev ワークフローで段階的に実装する。

## ディレクトリ構造

```
スライド作成ツール/
├── .claude/
│   ├── claude.md          # このファイル
│   ├── settings.json      # WebSearch/WebFetch自動承認
│   ├── whiteboard.md      # エージェント間情報共有（追記のみ）
│   ├── skills/
│   │   ├── spec-driven-dev/SKILL.md
│   │   ├── code-review/SKILL.md
│   │   └── error-handling-audit/SKILL.md
│   └── agents/
│       ├── researcher.md
│       ├── analyst.md
│       ├── fact-checker.md
│       └── devils-advocate.md
├── docs/                  # Phase A: 調査ドキュメント
├── references/            # 元資料・参考文献
├── src/                   # Phase B: 実装
│   ├── __init__.py
│   ├── config.py          # 設定・環境変数
│   ├── cli.py             # CLIエントリポイント
│   ├── document_reader.py # 資料読み込み（PDF/テキスト）
│   ├── slide_planner.py   # スライド構成生成（Gemini API）
│   ├── image_generator.py # 背景画像生成（Imagen 3）
│   ├── text_layout.py     # テキスト配置最適化（AI）
│   ├── pptx_builder.py    # PPTX組み立て
│   └── gemini_client.py   # Gemini APIクライアント
├── tests/
├── data/
│   └── output/            # 生成スライド出力先
├── .env.example
├── .gitignore
├── requirements.txt
├── PLANS.md               # 進捗・意思決定の記録
└── SPEC.md                # 実装仕様書（Phase B）
```

## 開発ルール

### コーディング規約
- コメントは日本語で書く
- 変数名・関数名は意味が明確な英語を使用
- 型ヒントを使用する（`def func(name: str) -> dict:`）
- 1関数は1つの責務に絞る
- マジックナンバーは `config.py` に定数として定義

### Git規約
- コミットメッセージ: `<type>(<scope>): <subject>`
  - type: feat / fix / docs / refactor / test
  - 日本語OK
- ブランチ: `feature/xxx`, `fix/xxx`
- コミット前に動作確認を実施すること

### セキュリティ
- APIキー・シークレットは `.env` に格納し、`.gitignore` で除外
- ハードコードされた認証情報は絶対に禁止
- ユーザー入力は必ずバリデーション / サニタイズする

### エラーハンドリング
- 例外を握りつぶさない（空のexcept禁止）
- 外部API呼び出しにはタイムアウトとリトライを設定
- ユーザーに見せるエラーメッセージは日本語で分かりやすく
- エラーログには原因特定に必要な情報を含める

### API連携ルール

#### 環境変数管理
```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY が設定されていません。.envファイルを確認してください。")
```

#### リトライ・タイムアウト
- 全API呼び出しに `timeout` を設定する（デフォルト: 30秒）
- 一時的なエラー（5xx, Timeout）は指数バックオフでリトライ（最大3回）
- レート制限エラー（429）はRetry-Afterヘッダに従う

## 調査ルール（Phase A）

### ソースと信頼性
- **全ての主張にソース（URL・出典）を必ず付ける**
- 一次ソース（公式ドキュメント・学術論文）を優先する
- 同じ情報を異なるソースでクロスチェックする
- 情報の鮮度（年度）に注意し、古いデータには明示する
- 優先ソース: Google AI 公式ドキュメント、python-pptx 公式ドキュメント、GitHub リポジトリ

### 分析姿勢
- 主張を無批判に受け入れない（批判的検証を徹底する）
- 具体的な数字・データを優先する（定性的な印象より定量的な根拠）
- 反例や不利なデータも公平に扱う

### 品質チェック
- 各ドキュメントは fact-checker で事実検証を実施
- 統合ドキュメント（Q4）は devils-advocate で論理攻撃を実施
- fact-checker → 修正反映 → devils-advocate の順序を守る（並列不可）

## レビューワークフロー

```
Phase A: researcher (並列OK) → 各doc作成 → whiteboard.md に発見サマリーを追記
         → analyst → Q4作成
         → fact-checker → 事実修正を各docに反映
         → devils-advocate → 設計判断のレビュー
```

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

## サブエージェントのWebSearch権限

`.claude/settings.json` の2層構成でWebSearch/WebFetchを自動承認する:

1. **`permissions.allow`**（静的許可）: バックグラウンドサブエージェント起動前の事前承認ステージで評価される
2. **`PreToolUse` フック**（動的許可）: ツール使用時に評価されるバックアップ

## 利用可能なスキル

- `skills/spec-driven-dev/` — 仕様書駆動の段階的開発ワークフロー（Phase B で使用）
- `skills/code-review/` — 多角的コードレビュー（Phase B で使用）
- `skills/error-handling-audit/` — エラーハンドリング監査（Phase B で使用）

## 利用可能なエージェント

- `agents/researcher.md` — Web調査（バックグラウンド並列実行可能）
- `agents/analyst.md` — 情報分析・技術比較（Q1〜Q3 完了後に実行）
- `agents/fact-checker.md` — 事実検証（事実修正の直接適用可能）
- `agents/devils-advocate.md` — 反論・論理攻撃

<!-- 重要: 各エージェント定義の「起動方法」セクションに記載された subagent_type と mode を使うこと。
     Explore タイプでは Write/Edit が使えず、ファイル出力が空になる。
     全エージェントは subagent_type: general-purpose, mode: bypassPermissions で起動する。 -->

## プロジェクト固有のルール

- Gemini API の応答が長すぎる場合はチャンク分割して処理する
- 生成するスライド枚数に上限は設けない（NotebookLM の15枚制限の解消が目的）
- PPTX テンプレートは `data/templates/` に格納可能にする（将来対応）
- CLI は対話モード（ステップ実行）を基本とし、バッチモードはオプション
