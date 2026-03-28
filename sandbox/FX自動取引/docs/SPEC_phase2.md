# FX自動取引システム — Phase 2 仕様書（ペーパートレード）

> 作成日: 2026-02-14
> 前提: Phase 1 完了（213テスト全パス）、MT5Client 実装済み
> ワークフロー: spec-driven-dev
> ブローカー: 外為ファイネスト + MetaTrader 5

---

## 1. 概要

- **目的**: MT5デモ口座を使った自動ペーパートレードを実現し、リアル取引移行前の検証を行う
- **Phase 2のゴール**: デモ口座で10分以上の連続自動取引が安定稼働し、キルスイッチが正常発動すること
- **前提条件**: MT5ターミナルがログイン済みの状態で起動していること

---

## 2. 機能一覧

| ID | 機能名 | ファイル | 依存 | 優先度 |
|----|--------|---------|------|--------|
| F11 | pip_value動的計算 | src/risk_manager.py 修正 | MT5Client | Must |
| F12 | ポジション管理 | src/position_manager.py 新規 | MT5Client | Must |
| F13 | トレーディングループ | src/trading_loop.py 新規 | F11, F12 | Must |
| F14 | 自動キルスイッチ連動 | risk_manager.py + trading_loop.py 修正 | F13 | Must |
| F15 | 戦略改善 | src/strategy/ 修正 or 新規 | F8（独立進行可） | Should |
| F16 | Phase 1送り項目 | 各ファイル修正 | F11 | Should |
| F17 | コードレビュー・統合テスト | tests/ + docs/ | F11〜F16 | Must |

---

## 3. 実装順序

```
MT5Client ✓（完了）
 │
 ├─→ F11（pip_value動的計算）──┐
 │                              │
 ├─→ F12（ポジション管理）────├─→ F13（トレーディングループ）
 │                              │         │
 │                              │         └─→ F14（キルスイッチ連動）
 │                              │
 └─→ F15（戦略改善）──────────┘
                                            │
                                     F16（送り項目消化）
                                            │
                                     F17（レビュー・テスト）
```

**並列化**: F11 / F12 / F15 は完全に独立 → 3並列実装可能

---

## 4. 各機能の詳細仕様

### F11: pip_value動的計算（`src/risk_manager.py` 修正）

**背景**: Phase 1 の `_get_pip_value()` はJPYクロス=10.0、非JPY=12.0の固定値。
実際のpip価値は為替レートにより変動するため、ブローカーから動的に取得する。

**修正対象**: `RiskManager._get_pip_value()`

**処理**:
1. BrokerClient を RiskManager に注入する（コンストラクタ引数追加）
2. `_get_pip_value(instrument)` を動的計算に変更:
   - JPYクロス: `1pip = 0.01`、pip_value = `0.01 * lot_size`（円建てなので直接）
   - 非JPYペア: `1pip = 0.0001`、pip_value = `0.0001 * lot_size * 決済通貨/JPYレート`
3. 為替レート取得失敗時は Phase 1 固定値にフォールバック（安全側）
4. `broker_client` 引数は Optional — None の場合は固定値を使用（テスト互換性維持）

**インターフェース変更**:

```python
class RiskManager:
    def __init__(
        self,
        account_balance: float,
        broker_client: Optional[BrokerClient] = None,  # 新規追加
    ) -> None:

    def _get_pip_value(
        self,
        instrument: str,
        lot_size: int = 1000,  # 新規追加: 1ロット=1,000通貨単位
    ) -> float:
        """
        通貨ペアごとの1pipあたりの金額（円建て）を動的に計算する。

        JPYクロス: 0.01 * lot_size（例: 1,000通貨 → 10円/pip）
        非JPYペア: 0.0001 * lot_size * 決済通貨JPYレート
                  （例: EUR/USD、lot_size=1,000、USD/JPY=150 → 15円/pip）

        broker_client が未設定 or レート取得失敗時は固定値フォールバック。
        """
```

**pip_value計算ロジック**:

| 通貨ペア | 1pipのサイズ | pip_value算出（lot_size通貨単位） |
|---------|-------------|-------------------------------|
| USD_JPY | 0.01 | `0.01 * lot_size` = 10.0（1,000通貨時） |
| EUR_JPY | 0.01 | `0.01 * lot_size` = 10.0 |
| EUR_USD | 0.0001 | `0.0001 * lot_size * USDJPY_rate` |
| GBP_USD | 0.0001 | `0.0001 * lot_size * USDJPY_rate` |
| AUD_USD | 0.0001 | `0.0001 * lot_size * USDJPY_rate` |

**フォールバック値**: JPYクロス=10.0、非JPYペア=12.0（Phase 1と同じ）

**エラーケース**:
- ブローカー未設定（`broker_client=None`） → 固定値を使用、WARNINGログ
- レート取得API失敗 → 固定値にフォールバック、WARNINGログ
- 取得レートが0以下（異常値） → 固定値にフォールバック、ERRORログ

**完了基準**:
- [ ] `_get_pip_value()` がブローカーから為替レートを取得して動的計算する
- [ ] JPYクロス・非JPYペアの両方で正しいpip_valueを返す
- [ ] ブローカー未設定時は固定値にフォールバックする
- [ ] レート取得失敗時は固定値にフォールバックする
- [ ] 既存テスト（65件）が全てパスする（後方互換性）
- [ ] 新規テスト（動的計算・フォールバック・エッジケース）がパスする

---

### F12: ポジション管理（`src/position_manager.py` 新規）

**背景**: トレーディングループで必要なポジションのライフサイクル管理。
ローカル状態とブローカー状態の照合を行い、不整合を検知する。

**クラス設計**:

```python
class PositionManagerError(Exception):
    """ポジション管理固有のエラー"""

class PositionManager:
    """
    ポジションのライフサイクル管理。
    ブローカーとの状態照合、上限管理、一括決済を提供する。
    """

    def __init__(
        self,
        broker_client: BrokerClient,
        risk_manager: RiskManager,
        max_positions: int = MAX_OPEN_POSITIONS,
    ) -> None:
        """
        Args:
            broker_client: ブローカーAPI
            risk_manager: リスク管理（ポジションサイジング、キルスイッチ参照）
            max_positions: 最大同時保有ポジション数
        """

    def open_position(
        self,
        instrument: str,
        signal: Signal,
        data: pd.DataFrame,
        strategy: StrategyBase,
    ) -> Optional[dict]:
        """
        シグナルに基づいてポジションを開く。

        1. キルスイッチチェック → 発動中なら None
        2. 同一通貨ペアの既存ポジション重複チェック
        3. 最大ポジション数チェック
        4. 損失上限チェック（RiskManager.check_loss_limits）
        5. 連続負けチェック（RiskManager.check_consecutive_losses）
        6. ポジションサイズ算出（RiskManager.calculate_position_size）
        7. SL/TP算出（strategy.calculate_stop_loss / calculate_take_profit）
        8. 成行注文発注（broker_client.market_order）
        9. ローカル状態を更新

        Args:
            instrument: 通貨ペア
            signal: BUY or SELL
            data: 価格データ（ATR算出用）
            strategy: 戦略インスタンス（SL/TP算出用）

        Returns:
            注文結果dict。取引不可時はNone。
        """

    def close_position(self, trade_id: str) -> Optional[dict]:
        """
        指定ポジションを決済する。

        Args:
            trade_id: 決済対象のトレードID

        Returns:
            決済結果dict。ポジションが見つからなければNone。
        """

    def close_all_positions(self, reason: str = "") -> list[dict]:
        """
        全ポジションを一括決済する。
        キルスイッチ EMERGENCY 発動時に呼ばれる。

        Returns:
            決済結果のリスト
        """

    def sync_with_broker(self) -> dict:
        """
        ブローカーの実ポジションとローカル状態を照合する。

        Returns:
            {"synced": int, "local_only": list, "broker_only": list}
            - synced: 一致件数
            - local_only: ローカルにのみ存在するtrade_id（決済済みの可能性）
            - broker_only: ブローカーにのみ存在するtrade_id（手動取引の可能性）
        """

    def get_open_positions(self) -> list[dict]:
        """ローカルの保有ポジション一覧を返す。"""

    @property
    def position_count(self) -> int:
        """現在の保有ポジション数"""

    @property
    def trade_history(self) -> list[dict]:
        """決済済みの取引履歴（損失上限チェック用）"""
```

**ローカルポジション状態の構造**:

```python
{
    "trade_id": str,
    "instrument": str,
    "units": int,         # 正=買い、負=売り
    "open_price": float,
    "stop_loss": float,
    "take_profit": float,
    "opened_at": datetime,
    "unrealized_pl": float,
}
```

**取引履歴（trade_history）の構造**:

```python
{
    "trade_id": str,
    "instrument": str,
    "units": int,
    "open_price": float,
    "close_price": float,
    "pl": float,          # 実現損益
    "opened_at": datetime,
    "close_time": datetime,
}
```

**エラーケース**:
- ブローカーAPI失敗 → PositionManagerError（握りつぶさない）
- 同一通貨ペアの重複ポジション → ログ出力 + None返却（安全側）
- 最大ポジション数超過 → ログ出力 + None返却
- sync_with_broker で不整合検出 → WARNINGログ、ローカル状態をブローカーに合わせる

**完了基準**:
- [ ] ポジションオープン → 決済のライフサイクルが正常動作する
- [ ] キルスイッチ発動時にポジションオープンが拒否される
- [ ] 最大ポジション数チェックが機能する
- [ ] sync_with_broker でローカル/ブローカーの不整合を検知できる
- [ ] close_all_positions で全ポジション一括決済できる
- [ ] trade_history が損失上限チェックに必要な情報を保持する
- [ ] テスト（モック使用）がパスする

---

### F13: トレーディングループ（`src/trading_loop.py` 新規）

**背景**: F11/F12 を統合し、戦略シグナルに基づく自動取引を連続実行する。

**クラス設計**:

```python
class TradingLoopError(Exception):
    """トレーディングループ固有のエラー"""

class TradingLoop:
    """
    メインの自動取引ループ。

    一定間隔で以下を繰り返す:
    1. 残高更新・ドローダウンチェック
    2. キルスイッチ監視
    3. ポジション同期
    4. 戦略シグナル取得
    5. シグナルに基づく注文実行
    """

    def __init__(
        self,
        broker_client: BrokerClient,
        position_manager: PositionManager,
        risk_manager: RiskManager,
        strategy: StrategyBase,
        instrument: str = "USD_JPY",
        granularity: str = MAIN_TIMEFRAME,
        check_interval_sec: int = 60,  # ループ間隔（秒）
    ) -> None:

    def start(self) -> None:
        """
        トレーディングループを開始する。

        KeyboardInterrupt または stop() で停止するまで無限ループ。
        各イテレーションで以下を実行:

        1. 口座残高を取得し RiskManager.update_balance()
        2. ドローダウンチェック → STOP/EMERGENCY ならキルスイッチ発動
        3. キルスイッチ発動中なら EMERGENCY 時は全決済、それ以外はスキップ
        4. ブローカーとのポジション同期
        5. 価格データ取得（直近100本）
        6. 戦略シグナル取得
        7. BUY/SELL なら PositionManager.open_position()
        8. check_interval_sec 秒待機
        9. 例外発生時: ログ出力、リトライ（致命的エラーなら停止）
        """

    def stop(self) -> None:
        """ループを安全に停止する。"""

    def run_once(self) -> Optional[dict]:
        """
        ループを1回だけ実行する（テスト用）。

        Returns:
            注文結果dict。取引なしの場合はNone。
        """

    @property
    def is_running(self) -> bool:
        """ループが実行中かどうか"""

    @property
    def iteration_count(self) -> int:
        """ループ実行回数"""

    @property
    def last_error(self) -> Optional[str]:
        """最後に発生したエラー（なければNone）"""
```

**ループ1イテレーションのフロー**:

```
┌──────────────────────────────────────┐
│ 1. 口座残高取得 → update_balance()   │
│ 2. ドローダウンチェック              │
│    └→ STOP/EMERGENCY → キルスイッチ  │
│ 3. キルスイッチ判定                  │
│    ├→ EMERGENCY: 全ポジション決済    │
│    └→ その他: 新規取引スキップ       │
│ 4. ポジション同期                    │
│ 5. 価格データ取得                    │
│ 6. 戦略シグナル取得                  │
│ 7. BUY/SELL → open_position()        │
│ 8. check_interval_sec 待機           │
└──────────────────────────────────────┘
```

**エラーハンドリング**:
- 一時エラー（API timeout、接続断）: ログ出力 + 次のイテレーションで自動リトライ
- 致命的エラー（認証失敗、MT5ターミナル停止）: ループ停止 + ERRORログ
- 全ての例外をキャッチしてログに記録（ループが予期せず死なないようにする）
- ただし例外を握りつぶさない: エラーカウンターで連続エラー回数を追跡し、閾値超過で停止

**設定値**:
- `check_interval_sec`: ループ間隔（デフォルト60秒）
- `max_consecutive_errors`: 連続エラー上限（デフォルト10回、超過でループ停止）

**完了基準**:
- [ ] `run_once()` が1イテレーション正常実行できる
- [ ] `start()` → `stop()` で安全に停止できる
- [ ] キルスイッチ発動時に新規取引がスキップされる
- [ ] EMERGENCY時に全ポジション決済が発動する
- [ ] 一時エラーでループが停止しない（リトライされる）
- [ ] 連続エラー上限超過でループが停止する
- [ ] テスト（モック使用）がパスする

---

### F14: 自動キルスイッチ連動（`src/risk_manager.py` + `src/trading_loop.py` 修正）

**背景**: Phase 1 のキルスイッチは手動発動のみ。ドローダウン STOP/EMERGENCY 到達時に自動発動するよう連動させる。

**修正内容**:

#### 1. RiskManager に自動キルスイッチ判定メソッド追加

```python
class RiskManager:
    def evaluate_kill_switch(
        self,
        current_balance: float,
        trade_history: list[dict],
        current_atr: Optional[float] = None,
        normal_atr: Optional[float] = None,
        current_spread: Optional[float] = None,
        normal_spread: Optional[float] = None,
    ) -> Optional[str]:
        """
        全キルスイッチ条件を評価し、発動すべき理由を返す。

        チェック順序（優先度順）:
        1. ドローダウン STOP/EMERGENCY → "daily_loss"
        2. 日次損失上限 → "daily_loss"
        3. 連続負け → "consecutive_losses"
        4. ボラティリティ（ATR） → "volatility"
        5. スプレッド → "spread"

        全条件クリアなら None。

        Returns:
            キルスイッチ理由（KillSwitch.VALID_REASONS のいずれか）。
            発動不要なら None。
        """
```

#### 2. TradingLoop でキルスイッチ自動判定を呼び出す

各イテレーションで `evaluate_kill_switch()` を呼び出し、結果に応じて:
- 理由が返された → `kill_switch.activate(reason)` → 自動発動
- None → 取引続行
- EMERGENCY → `position_manager.close_all_positions()` → 全決済

#### 3. キルスイッチ解除条件

- 日次損失キル: 翌日0:00 UTC以降に自動解除
- 連続負けキル: 24時間経過後に自動解除
- ボラティリティ/スプレッドキル: 条件が正常に戻ったら自動解除
- API切断キル: 再接続成功後に自動解除
- 手動キル: 手動解除のみ

```python
class KillSwitch:
    def should_auto_deactivate(self, current_time: datetime) -> bool:
        """自動解除すべきかどうかを判定する。"""

    # activated_at + 解除条件に基づく判定
```

**エラーケース**:
- evaluate_kill_switch 内で例外 → キルスイッチ発動（安全側）
- 全決済中に一部ポジションの決済失敗 → ログ出力、残りも試行する

**完了基準**:
- [ ] ドローダウン STOP 到達でキルスイッチが自動発動する
- [ ] ドローダウン EMERGENCY で全ポジション強制決済が実行される
- [ ] 日次損失上限到達でキルスイッチが自動発動する
- [ ] 5連敗でキルスイッチが自動発動する
- [ ] キルスイッチ解除条件が正しく動作する
- [ ] 既存テスト（65件）が全てパスする（後方互換性）
- [ ] 新規テスト（自動発動・解除）がパスする

---

### F15: 戦略改善（`src/strategy/` 修正 or 新規）

**背景**: Phase 1 のリアルデータバックテスト結果は SR > 1.0 が 0/15。
戦略パラメータの最適化 and/or 代替戦略の追加で改善を図る。

**進行方法**:
1. **Step 2-C**: researcher でMA戦略の改善手法・代替戦略を調査
2. **Step 2-C**: analyst で調査結果を評価・推奨策を選定
3. **Step 4**: 推奨に基づいて実装

**調査対象**:
- MA戦略のパラメータ最適化（期間、RSI閾値、ATR乗数）
- 代替エントリーフィルター（ボリンジャーバンド、MACD）
- 代替戦略（ブレイクアウト、ミーンリバージョン）
- 複数戦略の組み合わせ

**改善の評価基準**（backtester.py で検証）:
- SR > 1.0（最優先）
- DD < 20%（安全基準維持）
- WFE > 50%（過学習していない）
- 総トレード数 > 20（統計的に意味のある数）

**制約**:
- StrategyBase の3メソッドインターフェースを維持する
- 新戦略追加の場合は `src/strategy/` 配下に新ファイル
- RsiMaCrossoverBT のバックテストアダプタも対応させる

**完了基準**:
- [ ] researcher による調査レポート作成
- [ ] analyst による評価・推奨策の選定
- [ ] 推奨策に基づく実装（パラメータ変更 or 新戦略）
- [ ] バックテストで改善を確認（SR > 1.0 を目標）
- [ ] DD < 20% を維持
- [ ] 既存テスト（13件 ma_crossover + 5件 base）がパスする

---

### F16: Phase 1 送り項目（各ファイル修正）

Phase 1 レビューでPhase 2送りとなった5項目を消化する。

| ID | 内容 | 統合先 | 対象ファイル |
|----|------|--------|------------|
| M1 | pip_value動的計算 | **F11に統合済み** | risk_manager.py |
| M3 | fill_rate自動適用 | F13 | backtester.py + trading_loop.py |
| M4 | spread自動適用 | F13 | backtester.py |
| L1 | n_windows自動調整 | F15 | backtester.py |
| L2 | DD自動キルスイッチ | **F14に統合済み** | risk_manager.py |

#### M3: fill_rate自動適用

`BacktestEngine.run()` の結果に `apply_fill_rate_adjustment()` を自動適用するオプションを追加。

```python
def run(
    self,
    data, strategy_class,
    cash=1_000_000, spread=0.0, commission=0.0, margin=1.0,
    fill_rate: Optional[float] = None,  # 新規追加
) -> dict:
    result = ...  # 既存のバックテスト実行
    if fill_rate is not None:
        result = apply_fill_rate_adjustment(result, fill_rate)
    return result
```

#### M4: spread自動適用

`BacktestEngine.run()` で instrument と price が利用可能な場合、`calculate_spread()` を自動適用。

```python
def run(
    self,
    data, strategy_class,
    instrument: Optional[str] = None,  # 新規追加
    auto_spread: bool = False,         # 新規追加
    ...
) -> dict:
    if auto_spread and instrument:
        price = data["Close"].iloc[-1]
        spread = calculate_spread(instrument, price)
```

#### L1: n_windowsデータ量自動調整

`run_walk_forward()` で n_windows が大きすぎてセグメントが小さくなる場合に自動調整。

```python
def run_walk_forward(
    self, data, strategy_class, n_windows=5, auto_adjust=True, **kwargs
) -> dict:
    # n_windows自動調整: セグメントが最低60本になるよう調整
    min_segment = MA_LONG_PERIOD + 10
    max_possible_windows = len(data) // min_segment - 1
    if auto_adjust and n_windows > max_possible_windows > 0:
        logger.info(
            "n_windowsを自動調整: %d → %d（データ量不足）",
            n_windows, max_possible_windows,
        )
        n_windows = max_possible_windows
```

**完了基準**:
- [ ] M3: fill_rate オプション追加、自動適用が動作する
- [ ] M4: auto_spread オプション追加、自動適用が動作する
- [ ] L1: n_windows 自動調整が動作する
- [ ] 既存テスト（15件 backtester）が全てパスする
- [ ] 新規テスト（各オプション）がパスする

---

### F17: コードレビュー・統合テスト

**処理**:
1. code-review スキルで Phase 2 全コードをレビュー（4観点）
2. error-handling-audit スキルでエラーハンドリング監査（6カテゴリ）
3. Jenny で SPEC 準拠検証
4. task-completion-validator で動作検証
5. claude-md-compliance-checker で CLAUDE.md 規約準拠チェック
6. karen で現実チェック
7. カオステスト追加（MT5対応シナリオ）
8. 全テスト実行・合格確認

**カオステスト追加シナリオ**:

| # | シナリオ | 合格基準 |
|---|---------|---------|
| 7 | MT5ターミナル接続断 | キルスイッチ発動、再接続後にポジション照合 |
| 8 | ポジション不整合 | sync_with_broker で検知、ログ出力 |
| 9 | キルスイッチ自動発動 | DD STOP到達で自動停止、EMERGENCY で全決済 |

**完了基準**:
- [ ] code-review: Critical/High 未修正 0件
- [ ] error-handling-audit: 6カテゴリ全て A- 以上
- [ ] Jenny: SPEC 完了基準を全項目パス
- [ ] task-completion-validator: APPROVED
- [ ] karen: Phase 2 完了判定 合格
- [ ] カオステスト: 既存6 + 新規3 = 9シナリオ全合格
- [ ] 全テスト pass（Phase 1: 213 + Phase 2 新規）

---

## 5. データ構造（Phase 2 追加分）

### SQLite テーブル追加

#### trades テーブル（F12 で使用）

```sql
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL UNIQUE,
    instrument TEXT NOT NULL,
    units INTEGER NOT NULL,
    open_price REAL NOT NULL,
    close_price REAL,
    stop_loss REAL NOT NULL,
    take_profit REAL NOT NULL,
    pl REAL,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    status TEXT NOT NULL DEFAULT 'open'
);
```

#### kill_switch_log テーブル（F14 で使用）

```sql
CREATE TABLE IF NOT EXISTS kill_switch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reason TEXT NOT NULL,
    activated_at TEXT NOT NULL,
    deactivated_at TEXT,
    balance_at_activation REAL,
    drawdown_rate REAL
);
```

---

## 6. 成功基準

| 項目 | 基準 |
|------|------|
| テスト | 全テスト pass（Phase 1: 213 + Phase 2 新規） |
| コードレビュー | Critical/High 未修正 0件 |
| デモ口座接続 | MT5 デモ口座で発注→決済が正常動作 |
| トレーディングループ | 10分以上の連続稼働（クラッシュなし） |
| キルスイッチ | DD STOP/EMERGENCY で自動停止が発動 |
| 戦略 | SR > 1.0 または DD < 20% + WFE > 50% 維持 |
| Jenny検証 | SPEC完了基準を全項目パス |
| karen判定 | 「Phase 2 完了」の現実チェック合格 |

---

## 7. 実装進捗

- [x] F11: pip_value動的計算（13テスト追加、全パス）
- [x] F12: ポジション管理（17テスト追加、全パス）
- [x] F13: トレーディングループ（10テスト追加、全パス）
- [x] F14: 自動キルスイッチ連動（14テスト追加、全パス）
- [x] F15: 戦略改善（ADXフィルター追加、4テスト追加、全パス）
- [x] F16: Phase 1送り項目（M3/M4/L1、6テスト追加、全パス）
- [ ] F17: コードレビュー・統合テスト（最終検証中）
