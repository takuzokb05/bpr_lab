# Phase 1 → Phase 2 デプロイメント手順書

Phase 1（基盤構築）から Phase 2（ペーパートレード）への移行手順。

## 前提条件

- Phase 1 全機能（F1〜F9）が実装・テスト済み
- Phase 1→2 移行チェックリスト（後述）の全項目が Yes

## 1. 環境準備

### 1.1 Python環境

```bash
# Python 3.9+ がインストール済みであることを確認
python --version

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 1.2 環境変数の設定

```bash
# .env.example を .env にコピー
cp .env.example .env

# .env を編集し、以下を設定
# OANDA_API_KEY=<デモ口座のAPIキー>
# OANDA_ACCOUNT_ID=<デモ口座のID>
# OANDA_ENVIRONMENT=practice
```

**注意事項**:
- 最初は必ず `OANDA_ENVIRONMENT=practice`（デモ口座）で開始する
- `live` への切替は Phase 3 以降（最低3か月のペーパートレード実績必要）
- APIキーは `.gitignore` により Git 管理外

### 1.3 設定バリデーション

```bash
# 設定値のバリデーションを実行
python -c "from src.config import validate_or_raise; validate_or_raise()"
```

エラーが出た場合は `.env` ファイルの設定を確認する。

## 2. テスト実行

### 2.1 ユニットテスト

```bash
# 全テストを実行
python -m pytest tests/ -v

# 期待結果: 179 passed
```

### 2.2 カオステスト

```bash
# カオステストのみ実行
python -m pytest tests/chaos/ -v

# 期待結果: 14 passed（6シナリオ全合格）
```

## 3. バックテスト検証

### 3.1 ヒストリカルデータ取得

```python
from src.oanda_client import OandaClient
from src.data_collector import DataCollector

client = OandaClient()
with DataCollector(client) as dc:
    # USD/JPY 4時間足 500本を取得
    dc.fetch_and_store("USD_JPY", 500, "H4")

    # DBから読み込み
    df = dc.load_from_db("USD_JPY", "H4")
    print(f"取得済みデータ: {len(df)} 本")
```

### 3.2 バックテスト実行

```python
from src.backtester import BacktestEngine, RsiMaCrossoverBT, calculate_spread

with BacktestEngine() as engine:
    data = engine.prepare_data(df)
    spread = calculate_spread("USD_JPY", data["Close"].mean())

    # 単一バックテスト
    result = engine.run(data, RsiMaCrossoverBT, spread=spread)
    print(f"SR: {result['sharpe_ratio']}, DD: {result['max_drawdown']}%")

    # IS/OOS分割テスト
    ios = engine.run_in_out_sample(data, RsiMaCrossoverBT, spread=spread)
    print(f"WFE: {ios['wfe']}")

    # ウォークフォワード分析
    wf = engine.run_walk_forward(data, RsiMaCrossoverBT, n_windows=3, spread=spread)
    print(f"WFE平均: {wf['wfe_mean']}")

    # 結果を保存
    engine.save_result(result, "USD_JPY", "H4")
```

### 3.3 判定基準（doc 04 セクション6.4）

| 項目 | 基準 | 合否判定 |
|------|------|---------|
| WFE | > 50% (0.5) | バックテスト結果で確認 |
| シャープレシオ | > 1.0（年率換算） | バックテスト結果で確認 |
| 最大ドローダウン | < 20% | バックテスト結果で確認 |

**注意**: 合成データではなくリアルヒストリカルデータで判定すること。

## 4. Phase 2 への移行

### 4.1 移行チェックリスト

全項目が Yes であれば Phase 2 に移行可能。

| # | 項目 | 判定基準 | Yes/No |
|---|------|---------|--------|
| 1 | ユニットテスト全合格 | テストスイート100%パス | |
| 2 | カオステスト全合格 | 6シナリオ全て合格 | |
| 3 | バックテストWFE | WFE > 50% | |
| 4 | バックテストSR | シャープレシオ > 1.0 | |
| 5 | バックテスト最大DD | 最大ドローダウン < 20% | |
| 6 | コードレビューチェックリスト | 全項目確認済み | |
| 7 | デプロイメント手順書 | 作成済み・テスト済み | |

### 4.2 Phase 2 の概要

Phase 2ではペーパートレードを実施する:
- OANDA デモ口座で自動売買を最低3か月間実行
- 推奨トレード数: 100件以上（統計的有意性の最低基準）
- 主な追加実装:
  - リアルタイムトレーディングループ
  - 自動キルスイッチ連動
  - pip_value の動的計算
  - ポジション管理の自動化

## 5. 運用上の注意事項

### 5.1 安全に関する原則

- **資金管理が最優先**: 1トレードあたりの最大損失は口座資金の1%
- **キルスイッチ6種**: 日次損失/連続負け/ボラティリティ/スプレッド/API切断/手動
- **ドローダウン5段階制御**: 5%警告 → 10%半減 → 15%最小 → 20%停止 → 25%緊急
- **ペーパートレードで十分に検証**: リアル口座への移行は Phase 3 以降

### 5.2 リスクパラメータ（config.py で管理）

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| MAX_RISK_PER_TRADE | 1% | 1トレードあたりの最大リスク |
| MAX_LEVERAGE | 10倍 | 自主制限（法的上限25倍の40%） |
| MAX_DAILY_LOSS | 2% | 日次損失上限 |
| MAX_WEEKLY_LOSS | 5% | 週次損失上限 |
| MAX_MONTHLY_LOSS | 10% | 月次損失上限 |
| MAX_CONSECUTIVE_LOSSES | 5回 | 連続負け制限（24h停止） |

### 5.3 ログ確認

全ての操作は `logging` モジュールで記録される。キルスイッチ発動・ドローダウン検出は `WARNING` レベルで出力。

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 6. トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `OandaClientError: APIキーが設定されていません` | .env未設定 | .env ファイルに OANDA_API_KEY を設定 |
| `SystemExit: 設定エラー` | 設定値が不正 | エラーメッセージの指示に従い .env を修正 |
| `BacktestError: データ不足` | ヒストリカルデータが短い | count を増やしてデータを再取得 |
| テストが失敗する | 環境差異 | `pip install -r requirements.txt` を再実行 |
