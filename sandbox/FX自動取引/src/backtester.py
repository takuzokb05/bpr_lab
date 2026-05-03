"""
FX自動取引システム — バックテストエンジン

Backtesting.py をラップし、戦略のバックテスト・検証を実行する。
- イン・サンプル / アウト・オブ・サンプル分割（70:30）
- ウォークフォワード分析（WFE算出）
- パフォーマンス指標算出（SR, DD, 勝率, PF等）
- バックテスト結果のSQLite永続化
- スリッページ1pip、約定率80%の反映

SPEC.md F8 / doc 04 セクション6 準拠。
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy

from src.config import (
    ADX_PERIOD,
    ADX_THRESHOLD,
    ATR_MULTIPLIER,
    ATR_PERIOD,
    DB_PATH,
    MA_LONG_PERIOD,
    MA_SHORT_PERIOD,
    MIN_RISK_REWARD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    RSI_PERIOD,
)

logger = logging.getLogger(__name__)


class BacktestError(Exception):
    """バックテスト固有のエラー"""


# ------------------------------------------------------------------
# 戦略アダプタ: RsiMaCrossover → Backtesting.py Strategy
# ------------------------------------------------------------------


class RsiMaCrossoverBT(Strategy):
    """
    RSIフィルター付きMAクロスオーバー戦略の Backtesting.py アダプタ。

    src/strategy/ma_crossover.py の RsiMaCrossover と同等のロジックを、
    Backtesting.py の Strategy インターフェース（init/next）で実装する。

    クラス属性としてパラメータを定義し、optimize() での最適化にも対応可能。
    """

    # パラメータ（クラス属性 → optimize()対応）
    ma_short = MA_SHORT_PERIOD
    ma_long = MA_LONG_PERIOD
    rsi_period = RSI_PERIOD
    rsi_overbought = RSI_OVERBOUGHT
    rsi_oversold = RSI_OVERSOLD
    atr_period = ATR_PERIOD
    atr_multiplier = ATR_MULTIPLIER
    min_risk_reward = MIN_RISK_REWARD
    adx_period = ADX_PERIOD
    adx_threshold = ADX_THRESHOLD

    def init(self):
        """インジケータの事前計算。"""
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        # SMA
        self.ma_short_line = self.I(
            ta.sma, close, length=self.ma_short, name="SMA_short"
        )
        self.ma_long_line = self.I(
            ta.sma, close, length=self.ma_long, name="SMA_long"
        )

        # RSI
        self.rsi_line = self.I(
            ta.rsi, close, length=self.rsi_period, name="RSI"
        )

        # ATR
        self.atr_line = self.I(
            ta.atr, high, low, close, length=self.atr_period, name="ATR"
        )

        # ADX（F15追加）
        # pandas_ta.adx() は DataFrame を返すので、ADX列だけ取得するラッパー関数を使う
        adx_len = self.adx_period

        def _adx_only(high_s: pd.Series, low_s: pd.Series, close_s: pd.Series) -> pd.Series:
            """ADX DataFrameからADX列のみを抽出する"""
            result = ta.adx(high_s, low_s, close_s, length=adx_len)
            if result is not None:
                col = f"ADX_{adx_len}"
                if col in result.columns:
                    return result[col]
            return pd.Series([np.nan] * len(close_s))

        self.adx_line = self.I(
            _adx_only, high, low, close, name="ADX"
        )

    def next(self):
        """各バーでの取引ロジック。"""
        # インジケータ値を取得
        ma_short_curr = self.ma_short_line[-1]
        ma_long_curr = self.ma_long_line[-1]
        rsi_curr = self.rsi_line[-1]
        atr_curr = self.atr_line[-1]
        adx_curr = self.adx_line[-1]

        # NaN チェック
        if np.isnan(ma_short_curr) or np.isnan(ma_long_curr):
            return
        if np.isnan(rsi_curr) or np.isnan(atr_curr):
            return
        if np.isnan(adx_curr):
            return

        # ADXフィルター: トレンドが弱い場合はエントリーしない（F15追加）
        if adx_curr < self.adx_threshold:
            return

        # 前バー値（配列長が2未満なら判定不可）
        if len(self.ma_short_line) < 2:
            return
        ma_short_prev = self.ma_short_line[-2]
        ma_long_prev = self.ma_long_line[-2]
        if np.isnan(ma_short_prev) or np.isnan(ma_long_prev):
            return

        entry = self.data.Close[-1]

        # ゴールデンクロス + RSI < overbought → BUY
        if (
            ma_short_prev <= ma_long_prev
            and ma_short_curr > ma_long_curr
            and rsi_curr < self.rsi_overbought
        ):
            sl = entry - atr_curr * self.atr_multiplier
            risk = entry - sl
            tp = entry + risk * self.min_risk_reward
            self.buy(sl=sl, tp=tp)

        # デッドクロス + RSI > oversold → SELL
        elif (
            ma_short_prev >= ma_long_prev
            and ma_short_curr < ma_long_curr
            and rsi_curr > self.rsi_oversold
        ):
            sl = entry + atr_curr * self.atr_multiplier
            risk = sl - entry
            tp = entry - risk * self.min_risk_reward
            self.sell(sl=sl, tp=tp)


# ------------------------------------------------------------------
# ヘルパー関数
# ------------------------------------------------------------------


def apply_fill_rate_adjustment(
    result: dict[str, Any], fill_rate: float = 0.8
) -> dict[str, Any]:
    """
    約定率を考慮してメトリクスを補正する。

    全トレードを実行した結果に補正係数を適用し、
    raw_* と adjusted_* の両方を保持する。

    Args:
        result: run() の戻り値
        fill_rate: 約定率（0.8 = 80%）

    Returns:
        補正済みのresult dict
    """
    result["fill_rate"] = fill_rate
    result["raw_total_trades"] = result.get("total_trades")
    result["raw_return_pct"] = result.get("return_pct")
    result["raw_sharpe_ratio"] = result.get("sharpe_ratio")

    if result.get("total_trades") is not None:
        result["adjusted_total_trades"] = int(result["total_trades"] * fill_rate)

    if result.get("return_pct") is not None:
        result["adjusted_return_pct"] = result["return_pct"] * fill_rate

    if result.get("sharpe_ratio") is not None:
        result["adjusted_sharpe_ratio"] = result["sharpe_ratio"] * (fill_rate ** 0.5)

    return result


# 通貨ペア別の実測スプレッド + スリッページ合算 (pips)
# 根拠: P2-D 本番ログ解析 (docs/gbp_jpy_slippage_analysis.md) +
#       P1-2 yfinance 比較 (docs/live_vs_backtest_diff.md)
#   - USD_JPY: P1-2 avg 0.94 pips → 1.5 pips（外れ値耐性込み）
#   - EUR_USD: P1-2 avg 1.96 pips → 2.0 pips
#   - GBP_JPY: P2-D avg 1.80 pips, P1-2 avg 3.51 pips → 2.5 pips（中庸）
# 未測定ペアは 2.0 pips を保守的デフォルトとする（PR #7 以前の 1.0 pips は楽観的すぎた）。
TYPICAL_SPREADS_PIPS: dict[str, float] = {
    "USD_JPY": 1.5,
    "EUR_USD": 2.0,
    "GBP_JPY": 2.5,
}
DEFAULT_SPREAD_PIPS: float = 2.0


def calculate_spread(
    instrument: str, price: float, pip_spread: float | None = None
) -> float:
    """
    スリッページ用のspread値（相対値）を算出する。

    Args:
        instrument: 通貨ペア（例: "USD_JPY", "EUR_USD"）
        price: 代表価格（例: 150.0）
        pip_spread: スプレッド幅（pip単位）。省略時はペア別実測値
                    (TYPICAL_SPREADS_PIPS) または DEFAULT_SPREAD_PIPS を使用

    Returns:
        Backtesting.py の spread パラメータ（相対値）
    """
    if pip_spread is None:
        pip_spread = TYPICAL_SPREADS_PIPS.get(
            instrument.upper(), DEFAULT_SPREAD_PIPS,
        )

    if "JPY" in instrument.upper():
        pip_value = 0.01
    else:
        pip_value = 0.0001

    return (pip_value * pip_spread) / price


# ------------------------------------------------------------------
# バックテストエンジン
# ------------------------------------------------------------------


class BacktestEngine:
    """
    Backtesting.py をラップするバックテストエンジン。

    - 単一バックテストの実行
    - In-Sample / Out-of-Sample 分割テスト
    - ウォークフォワード分析（WFE算出）
    - バックテスト結果の SQLite 永続化
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        """
        Args:
            db_path: SQLite データベースのパス。省略時は config.DB_PATH。
                     ":memory:" でインメモリDB（テスト用）。
        """
        self._db_path = db_path if db_path is not None else DB_PATH
        self._is_memory = str(self._db_path) == ":memory:"

        if not self._is_memory:
            self._db_path = Path(self._db_path)
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._persistent_conn: sqlite3.Connection | None = None
        if self._is_memory:
            self._persistent_conn = sqlite3.connect(":memory:")

        self._init_db()
        logger.info("BacktestEngineを初期化しました（DB: %s）", self._db_path)

    def close(self) -> None:
        """永続コネクションを閉じる。"""
        if self._persistent_conn is not None:
            self._persistent_conn.close()
            self._persistent_conn = None
            logger.info("BacktestEngineの永続コネクションを閉じました")

    def __enter__(self) -> "BacktestEngine":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _get_connection(self) -> sqlite3.Connection:
        if self._persistent_conn is not None:
            return self._persistent_conn
        return sqlite3.connect(str(self._db_path))

    def _close_connection(self, conn: sqlite3.Connection) -> None:
        if conn is not self._persistent_conn:
            conn.close()

    def _init_db(self) -> None:
        """backtest_results テーブルを作成する。"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS backtest_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument TEXT NOT NULL,
            granularity TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            run_type TEXT NOT NULL,
            run_at TEXT NOT NULL,
            sharpe_ratio REAL,
            max_drawdown REAL,
            win_rate REAL,
            profit_factor REAL,
            total_trades INTEGER,
            wfe REAL,
            return_pct REAL,
            params_json TEXT,
            metrics_json TEXT
        );
        """
        conn = self._get_connection()
        try:
            conn.execute(create_sql)
            conn.commit()
        except sqlite3.Error as e:
            raise BacktestError(f"DBの初期化に失敗しました: {e}") from e
        finally:
            self._close_connection(conn)

    # ------------------------------------------------------------------
    # データ準備
    # ------------------------------------------------------------------

    @staticmethod
    def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameを Backtesting.py 用に変換する。

        - カラム名を小文字 → 大文字に変換（open → Open）
        - NaN 行を除去

        Args:
            df: OHLCV形式のDataFrame（小文字カラム名）

        Returns:
            変換済みDataFrame（大文字カラム名、NaN除去済み）

        Raises:
            BacktestError: 変換後にデータが空の場合
        """
        if df.empty:
            raise BacktestError("入力データが空です")

        df_out = df.copy()
        df_out.columns = [col.capitalize() for col in df_out.columns]

        before_len = len(df_out)
        df_out.dropna(inplace=True)
        after_len = len(df_out)

        if before_len > after_len:
            logger.warning(
                "NaN行を %d 行除去しました（%d → %d）",
                before_len - after_len,
                before_len,
                after_len,
            )

        if df_out.empty:
            raise BacktestError("NaN除去後にデータが空になりました")

        return df_out

    # ------------------------------------------------------------------
    # バックテスト実行
    # ------------------------------------------------------------------

    def run(
        self,
        data: pd.DataFrame,
        strategy_class: type[Strategy],
        cash: float = 1_000_000,
        spread: float = 0.0,
        commission: float = 0.0,
        margin: float = 1.0,
        fill_rate: Optional[float] = None,
        instrument: Optional[str] = None,
        auto_spread: bool = False,
    ) -> dict[str, Any]:
        """
        単一バックテストを実行する。

        Args:
            data: OHLCV DataFrame（大文字カラム名、prepare_data()済み）
            strategy_class: Backtesting.py Strategy サブクラス
            cash: 初期資金（デフォルト100万円）
            spread: スリッページ（相対値）
            commission: 手数料（相対値）
            margin: 証拠金率（1.0 = レバレッジなし）
            fill_rate: 約定率（例: 0.8 = 80%）。指定時はメトリクスを補正する
            instrument: 通貨ペア（例: "USD_JPY"）。auto_spread使用時に必要
            auto_spread: Trueの場合、instrumentから自動でspreadを計算する。
                         手動でspreadが指定されている場合（spread != 0.0）は手動値を優先

        Returns:
            バックテスト結果dict

        Raises:
            BacktestError: バックテスト実行に失敗した場合
        """
        # M4: auto_spread が True で instrument 指定あり → spread を自動計算
        if auto_spread and instrument and spread == 0.0:
            price = float(data["Close"].iloc[-1])
            spread = calculate_spread(instrument, price)
            logger.info(
                "spread自動計算: instrument=%s, price=%.5f, spread=%.8f",
                instrument, price, spread,
            )

        if len(data) < MA_LONG_PERIOD + 10:
            raise BacktestError(
                f"データ不足: 最低 {MA_LONG_PERIOD + 10} 本必要です"
                f"（現在 {len(data)} 本）"
            )

        try:
            bt = Backtest(
                data,
                strategy_class,
                cash=cash,
                spread=spread,
                commission=commission,
                margin=margin,
                exclusive_orders=True,
            )
            stats = bt.run()
        except Exception as e:
            raise BacktestError(f"バックテストの実行に失敗しました: {e}") from e

        result = self._extract_metrics(stats)

        # M3: fill_rate 自動適用
        if fill_rate is not None:
            result = apply_fill_rate_adjustment(result, fill_rate)

        logger.info(
            "バックテスト完了: SR=%.2f, DD=%.2f%%, WR=%.1f%%, PF=%.2f, Trades=%d",
            result.get("sharpe_ratio") or 0,
            result.get("max_drawdown") or 0,
            result.get("win_rate") or 0,
            result.get("profit_factor") or 0,
            result.get("total_trades") or 0,
        )

        return result

    def run_in_out_sample(
        self,
        data: pd.DataFrame,
        strategy_class: type[Strategy],
        split_ratio: float = 0.7,
        **kwargs,
    ) -> dict[str, Any]:
        """
        In-Sample / Out-of-Sample 分割バックテストを実行する。

        Args:
            data: OHLCV DataFrame（大文字カラム名）
            strategy_class: Strategy サブクラス
            split_ratio: IS比率（0.7 = 70:30分割）
            **kwargs: run() に渡すパラメータ（cash, spread等）

        Returns:
            dict: in_sample結果, out_of_sample結果, wfe

        Raises:
            BacktestError: データ不足の場合
        """
        min_is = MA_LONG_PERIOD + 10
        split_idx = int(len(data) * split_ratio)

        if split_idx < min_is:
            raise BacktestError(
                f"IS データ不足: {split_idx} 本 < 最低 {min_is} 本"
            )
        if len(data) - split_idx < min_is:
            raise BacktestError(
                f"OOS データ不足: {len(data) - split_idx} 本 < 最低 {min_is} 本"
            )

        data_is = data.iloc[:split_idx]
        data_oos = data.iloc[split_idx:]

        logger.info(
            "IS/OOS分割: IS=%d本, OOS=%d本（比率=%.2f）",
            len(data_is), len(data_oos), split_ratio,
        )

        result_is = self.run(data_is, strategy_class, **kwargs)
        result_oos = self.run(data_oos, strategy_class, **kwargs)

        wfe = self._calculate_wfe(
            result_is.get("sharpe_ratio"),
            result_oos.get("sharpe_ratio"),
        )

        return {
            "in_sample": result_is,
            "out_of_sample": result_oos,
            "wfe": wfe,
        }

    def run_walk_forward(
        self,
        data: pd.DataFrame,
        strategy_class: type[Strategy],
        n_windows: int = 5,
        auto_adjust: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """
        ウォークフォワード分析を実行する。

        データを(n_windows+1)等分し、拡張ウィンドウでIS/OOSテストを繰り返す。
        WFE = mean(OOS_SR / IS_SR)。

        Args:
            data: OHLCV DataFrame（大文字カラム名）
            strategy_class: Strategy サブクラス
            n_windows: ウィンドウ数（デフォルト5）
            auto_adjust: Trueの場合、データ量に応じてn_windowsを自動縮小する
            **kwargs: run() に渡すパラメータ

        Returns:
            dict: windows（各結果）, wfe_mean

        Raises:
            BacktestError: セグメントサイズ不足の場合（auto_adjust=Falseまたは調整不可）
        """
        total_bars = len(data)
        segment_size = total_bars // (n_windows + 1)
        min_segment = MA_LONG_PERIOD + 10

        # L1: n_windows 自動調整
        if auto_adjust and segment_size < min_segment:
            max_possible_windows = total_bars // min_segment - 1
            if max_possible_windows > 0:
                logger.info(
                    "n_windowsを自動調整: %d → %d（データ量不足）",
                    n_windows, max_possible_windows,
                )
                n_windows = max_possible_windows
                segment_size = total_bars // (n_windows + 1)
            else:
                raise BacktestError(
                    f"データ不足: 最低1ウィンドウ分のデータが必要です"
                    f"（現在 {total_bars} 本）"
                )

        if segment_size < min_segment:
            raise BacktestError(
                f"データ不足: 各セグメントに最低 {min_segment} 本必要です"
                f"（現在 {segment_size} 本、全体 {total_bars} 本、{n_windows} ウィンドウ）"
            )

        windows_results = []
        wfe_list = []

        for i in range(n_windows):
            is_end = (i + 1) * segment_size
            oos_end = min((i + 2) * segment_size, total_bars)

            data_is = data.iloc[:is_end]
            data_oos = data.iloc[is_end:oos_end]

            logger.info(
                "ウィンドウ %d/%d: IS=%d本, OOS=%d本",
                i + 1, n_windows, len(data_is), len(data_oos),
            )

            result_is = self.run(data_is, strategy_class, **kwargs)
            result_oos = self.run(data_oos, strategy_class, **kwargs)

            wfe = self._calculate_wfe(
                result_is.get("sharpe_ratio"),
                result_oos.get("sharpe_ratio"),
            )
            if wfe is not None:
                wfe_list.append(wfe)

            windows_results.append({
                "window": i + 1,
                "in_sample": result_is,
                "out_of_sample": result_oos,
                "wfe": wfe,
            })

        wfe_mean = float(np.mean(wfe_list)) if wfe_list else None

        logger.info(
            "ウォークフォワード完了: WFE平均=%.2f（%d/%d ウィンドウ有効）",
            wfe_mean or 0, len(wfe_list), n_windows,
        )

        return {
            "windows": windows_results,
            "wfe_mean": wfe_mean,
        }

    # ------------------------------------------------------------------
    # メトリクス抽出
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_metrics(stats: pd.Series) -> dict[str, Any]:
        """Backtesting.py の Stats から主要メトリクスを抽出する。"""

        def _safe_get(key: str) -> Optional[float]:
            val = stats.get(key)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                return None
            return float(val)

        return {
            "sharpe_ratio": _safe_get("Sharpe Ratio"),
            "max_drawdown": _safe_get("Max. Drawdown [%]"),
            "win_rate": _safe_get("Win Rate [%]"),
            "profit_factor": _safe_get("Profit Factor"),
            "total_trades": int(stats.get("# Trades", 0)),
            "return_pct": _safe_get("Return [%]"),
            "equity_final": _safe_get("Equity Final [$]"),
            "sortino_ratio": _safe_get("Sortino Ratio"),
            "calmar_ratio": _safe_get("Calmar Ratio"),
            "avg_trade_pct": _safe_get("Avg. Trade [%]"),
            "sqn": _safe_get("SQN"),
        }

    @staticmethod
    def _calculate_wfe(
        sr_is: Optional[float], sr_oos: Optional[float]
    ) -> Optional[float]:
        """WFE（ウォークフォワード効率）を計算する。"""
        if sr_is is None or sr_oos is None or sr_is == 0:
            return None
        wfe = sr_oos / sr_is
        # 異常値チェック: 数値として有限でなければNone
        if not np.isfinite(wfe):
            logger.warning(
                "異常なWFE値を検出: sr_is=%.4f, sr_oos=%.4f。Noneを返します。",
                sr_is, sr_oos,
            )
            return None
        return wfe

    # ------------------------------------------------------------------
    # 結果の永続化
    # ------------------------------------------------------------------

    def save_result(
        self,
        result: dict[str, Any],
        instrument: str,
        granularity: str,
        strategy_name: str = "RsiMaCrossover",
        run_type: str = "single",
    ) -> None:
        """
        バックテスト結果を SQLite に保存する。

        Args:
            result: run() / run_in_out_sample() / run_walk_forward() の戻り値
            instrument: 通貨ペア
            granularity: 時間足
            strategy_name: 戦略名
            run_type: "single" / "walk_forward"
        """
        insert_sql = """
        INSERT INTO backtest_results
            (instrument, granularity, strategy_name, run_type, run_at,
             sharpe_ratio, max_drawdown, win_rate, profit_factor, total_trades,
             wfe, return_pct, params_json, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        run_at = datetime.now(timezone.utc).isoformat()

        if run_type == "walk_forward":
            sr = None
            dd = None
            wr = None
            pf = None
            trades = None
            wfe = result.get("wfe_mean")
            ret = None
        else:
            sr = result.get("sharpe_ratio")
            dd = result.get("max_drawdown")
            wr = result.get("win_rate")
            pf = result.get("profit_factor")
            trades = result.get("total_trades")
            wfe = result.get("wfe")
            ret = result.get("return_pct")

        metrics_json = json.dumps(result, default=str)
        params_json = json.dumps({})

        conn = self._get_connection()
        try:
            conn.execute(
                insert_sql,
                (instrument, granularity, strategy_name, run_type, run_at,
                 sr, dd, wr, pf, trades, wfe, ret, params_json, metrics_json),
            )
            conn.commit()
            logger.info(
                "バックテスト結果を保存: %s/%s/%s/%s",
                instrument, granularity, strategy_name, run_type,
            )
        except sqlite3.Error as e:
            raise BacktestError(f"結果の保存に失敗しました: {e}") from e
        finally:
            self._close_connection(conn)

    def load_results(
        self,
        instrument: str,
        granularity: str,
        strategy_name: str = "RsiMaCrossover",
    ) -> list[dict[str, Any]]:
        """
        保存済みバックテスト結果を読み込む。

        Args:
            instrument: 通貨ペア
            granularity: 時間足
            strategy_name: 戦略名

        Returns:
            結果リスト（新しい順）
        """
        query_sql = """
        SELECT id, instrument, granularity, strategy_name, run_type, run_at,
               sharpe_ratio, max_drawdown, win_rate, profit_factor, total_trades,
               wfe, return_pct, params_json, metrics_json
        FROM backtest_results
        WHERE instrument = ? AND granularity = ? AND strategy_name = ?
        ORDER BY run_at DESC
        """

        conn = self._get_connection()
        try:
            cursor = conn.execute(query_sql, (instrument, granularity, strategy_name))
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            raise BacktestError(f"結果の読み込みに失敗しました: {e}") from e
        finally:
            self._close_connection(conn)

        columns = [
            "id", "instrument", "granularity", "strategy_name", "run_type",
            "run_at", "sharpe_ratio", "max_drawdown", "win_rate",
            "profit_factor", "total_trades", "wfe", "return_pct",
            "params_json", "metrics_json",
        ]

        results = []
        for row in rows:
            r = dict(zip(columns, row))
            r["params"] = json.loads(r.pop("params_json"))
            r["metrics"] = json.loads(r.pop("metrics_json"))
            results.append(r)

        logger.info(
            "バックテスト結果を読み込み: %s/%s/%s, %d件",
            instrument, granularity, strategy_name, len(results),
        )

        return results
