"""Phase 2 BT: 候補 #12 Cointegration Pairs Trading

仕様:
- 2 通貨ペアの cointegration 検定 (Engle-Granger, statsmodels.tsa.stattools.coint)
- z-score 反転で取引 (entry |z|>=2.0, exit |z|<=0.5, stop |z|>=4.0)
- 6 ヶ月ローリングで cointegration 再評価 (p<0.05 維持できないペアは取引停止)
- ペア候補: EUR_USD/GBP_USD, AUD_USD/NZD_USD, USD_CHF/USD_CAD など (EUR_CHF 除外)
- 過去 5 年 D1
- スプレッド 2 ペア分 (両建てで 2倍効く)
- スワップ実数値計算 (長期保有想定)
- Black Swan ストレステスト: 2020-03 COVID, 2024-07/08 円介入, 2022 年末乱高下
- Walk-Forward: 12 ヶ月学習 / 3 ヶ月運用、複数 window

入力: data/mt5_<pair>_D1_5y.csv (7 ペア)
出力:
- data/_phase2_bt_12_cointegration_trades.csv
- data/_phase2_bt_12_cointegration_monthly.csv
- data/_phase2_bt_12_cointegration_stress.csv
- data/_phase2_bt_12_cointegration_pairs.csv (p値マトリックス)
"""
from __future__ import annotations
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

# =================================================================
# 定数
# =================================================================

DATA_DIR = ROOT / "data"

# ペア候補 (EUR_CHF 等 CHF クロスは除外: 2015 SNB 後構造変化)
INSTRUMENTS = ["EUR_USD", "GBP_USD", "AUD_USD", "NZD_USD", "USD_CHF", "USD_CAD", "USD_JPY"]

# 取引する候補ペア (ファンダメンタル近接 + 流動性高)
# (左=Long側基準, 右=Short側基準)
CANDIDATE_PAIRS = [
    ("EUR_USD", "GBP_USD"),  # 欧州通貨
    ("AUD_USD", "NZD_USD"),  # オセアニア
    ("USD_CAD", "AUD_USD"),  # コモディティ通貨
    ("EUR_USD", "USD_CHF"),  # 逆相関 (両方欧州)
    ("GBP_USD", "AUD_USD"),  # G7-リスク通貨
    ("USD_CHF", "USD_CAD"),  # 安全 vs 商品
]

# 戦略パラメータ
COINT_PVAL_THRESHOLD = 0.05  # 取引採用条件
ZSCORE_LOOKBACK = 60  # z-score 計算ウィンドウ (D1 = 60 日)
ENTRY_Z = 2.0
EXIT_Z = 0.5
STOP_Z = 4.0
MAX_HOLD_DAYS = 30  # 時間ストップ (D1 で 30 バー)

# WFA / ローリング
COINT_TEST_WINDOW_DAYS = 180  # 6 ヶ月 (D1 で 180 バー)
COINT_REEVAL_INTERVAL_DAYS = 7  # 週次再評価
WFA_TRAIN_DAYS = 365  # 12 ヶ月学習
WFA_TEST_DAYS = 180  # 6 ヶ月運用 (3ヶ月は短すぎて trade=0 続出)

# コスト (ペア別実測ベース、エントリー時のスプレッド + スリッページ)
# pip = 0.0001 for USD pairs, 0.01 for JPY pairs
# 外為ファイネスト MT5 実測 (符号は pip 単位)
SPREAD_PIPS = {
    "EUR_USD": 0.5,
    "GBP_USD": 0.9,
    "AUD_USD": 0.6,
    "NZD_USD": 0.7,   # 概算
    "USD_CHF": 0.7,   # 概算
    "USD_CAD": 0.8,   # 概算
    "USD_JPY": 0.2,
}
SLIPPAGE_PIPS_ENTRY = 1.0
SLIPPAGE_PIPS_EXIT = 1.0

# スワップ (年率 %、約定単価あたり、ロングが取る方は + ショートが取る方は -)
# 2024-2026 を想定した保守値。実測は外為ファイネスト公開表より概算
# ロングUSD = + (米金利 4.5%), ロングEUR = - (欧金利 3.5%) など
# スプレッド計算用に通貨ペアごとのロングスワップ (年率%) を保持
LONG_SWAP_PCT = {
    "EUR_USD": -1.5,   # EUR ロング = 不利 (USD金利>EUR金利)
    "GBP_USD": -0.5,   # GBP ロング = やや不利
    "AUD_USD": -1.5,   # AUD ロング = 不利
    "NZD_USD": -0.8,
    "USD_CHF": +3.0,   # USD ロング = 有利
    "USD_CAD": +0.5,
    "USD_JPY": +4.5,   # USD ロング = 有利 (キャリー)
}
# ショートは符号反転 + ブローカー控除 (1.5% 想定)
SHORT_SWAP_PENALTY = 1.5  # 年率 %, brokerが取る分

# 取引サイズ
LOT_SIZE = 100_000  # 1 ロット = 10 万通貨
TRADE_VOLUME_LOTS = 0.10  # 0.1 ロット = 1 万通貨
INITIAL_CAPITAL_JPY = 1_000_000

# キルスイッチ
DAILY_LOSS_LIMIT_PCT = -3.0   # 日次 -3% で警告 / 半量化
DAILY_LOSS_HARD_STOP_PCT = -5.0  # -5% で停止
MONTHLY_LOSS_LIMIT_PCT = -10.0   # 月次 -10%

# 為替仮定 (簡易): USD/JPY 等の為替仮定で JPY 換算
USDJPY_REF = 150.0  # 機会費用比較用、ざっくり
EURUSD_REF = 1.08
GBPUSD_REF = 1.27
AUDUSD_REF = 0.65
NZDUSD_REF = 0.60
USDCHF_REF = 0.90
USDCAD_REF = 1.36


def pip_size(instrument: str) -> float:
    """通貨ペアの 1 pip サイズ (価格単位)"""
    return 0.01 if instrument.endswith("_JPY") else 0.0001


def get_quote_to_jpy(instrument: str, mid_price: float) -> float:
    """quote currency を JPY に変換するレート

    例: EUR_USD なら USD->JPY = 150
        USD_JPY なら JPY->JPY = 1.0
        USD_CAD なら CAD->JPY = USDJPY / USDCAD = 150 / 1.36 ≈ 110
    """
    quote = instrument.split("_")[1]
    if quote == "JPY":
        return 1.0
    if quote == "USD":
        return USDJPY_REF
    if quote == "CHF":
        return USDJPY_REF / USDCHF_REF
    if quote == "CAD":
        return USDJPY_REF / USDCAD_REF
    # EUR, GBP, AUD, NZD: quote currency 経由
    if quote == "EUR":
        return USDJPY_REF * EURUSD_REF
    if quote == "GBP":
        return USDJPY_REF * GBPUSD_REF
    if quote == "AUD":
        return USDJPY_REF * AUDUSD_REF
    if quote == "NZD":
        return USDJPY_REF * NZDUSD_REF
    return USDJPY_REF  # fallback


# =================================================================
# データロード
# =================================================================


def load_pair_data() -> dict[str, pd.DataFrame]:
    """全 7 ペアの D1 データをロード、共通インデックスに揃える"""
    data = {}
    for inst in INSTRUMENTS:
        path = DATA_DIR / f"mt5_{inst}_D1_5y.csv"
        df = pd.read_csv(path, parse_dates=["datetime"]).set_index("datetime").sort_index()
        df.index = df.index.tz_convert("UTC") if df.index.tz else df.index.tz_localize("UTC")
        data[inst] = df

    # 共通日付に揃える
    common_idx = None
    for inst, df in data.items():
        if common_idx is None:
            common_idx = df.index
        else:
            common_idx = common_idx.intersection(df.index)
    print(f"共通日数: {len(common_idx)}  期間: {common_idx[0]} -> {common_idx[-1]}")

    for inst in INSTRUMENTS:
        data[inst] = data[inst].loc[common_idx]
    return data


# =================================================================
# Cointegration テスト
# =================================================================


def estimate_hedge_ratio(y: pd.Series, x: pd.Series) -> float:
    """OLS で hedge ratio (β) 推定: y = α + β*x"""
    X = add_constant(x.values)
    model = OLS(y.values, X).fit()
    return float(model.params[1])


def coint_test(y: pd.Series, x: pd.Series) -> dict:
    """Engle-Granger 共和分検定

    Returns: {'pvalue', 'tstat', 'beta'}
    """
    try:
        tstat, pval, _ = coint(y.values, x.values, trend="c")
        beta = estimate_hedge_ratio(y, x)
        return {"pvalue": float(pval), "tstat": float(tstat), "beta": beta}
    except Exception as e:
        return {"pvalue": np.nan, "tstat": np.nan, "beta": np.nan, "error": str(e)}


def cointegration_matrix(data: dict[str, pd.DataFrame], window_start: pd.Timestamp,
                         window_end: pd.Timestamp) -> pd.DataFrame:
    """指定期間で全ペア組合せの cointegration p値を計算"""
    insts = list(data.keys())
    rows = []
    for i, a in enumerate(insts):
        for j, b in enumerate(insts):
            if i >= j:
                continue
            sa = data[a].loc[window_start:window_end, "close"]
            sb = data[b].loc[window_start:window_end, "close"]
            if len(sa) < 30 or len(sb) < 30:
                continue
            res = coint_test(sa, sb)
            rows.append({
                "pair_a": a, "pair_b": b,
                "window_start": window_start, "window_end": window_end,
                "n": len(sa),
                "pvalue": res["pvalue"],
                "tstat": res["tstat"],
                "beta": res["beta"],
                "is_cointegrated": (not np.isnan(res["pvalue"])) and (res["pvalue"] < COINT_PVAL_THRESHOLD),
            })
    return pd.DataFrame(rows)


# =================================================================
# 取引シミュレーション
# =================================================================


@dataclass
class Position:
    pair_a: str
    pair_b: str
    direction: int  # +1: long spread (long A, short B), -1: short spread
    beta: float
    open_time: pd.Timestamp
    open_price_a: float
    open_price_b: float
    volume_lots_a: float
    volume_lots_b: float
    entry_z: float
    bars_held: int = 0
    swap_accumulated_jpy: float = 0.0


def compute_zscore(spread: pd.Series, lookback: int) -> pd.Series:
    """z-score = (spread - rolling mean) / rolling std"""
    mean = spread.rolling(lookback).mean()
    std = spread.rolling(lookback).std(ddof=0)
    z = (spread - mean) / std
    return z


def compute_pip_value_jpy(instrument: str, lots: float, mid_price: float) -> float:
    """1 pip 当たりの JPY 損益 (ロット数 × 100,000 × pip_size × quote→JPY レート)"""
    ps = pip_size(instrument)
    units = lots * LOT_SIZE
    # USD 系: 1 pip = units * 0.0001 quote_currency
    # JPY 系: 1 pip = units * 0.01 quote_currency = units * 0.01 JPY
    quote_per_pip = units * ps
    return quote_per_pip * get_quote_to_jpy(instrument, mid_price)


def compute_spread_cost_jpy(instrument: str, lots: float, mid_price: float) -> float:
    """エントリー時のスプレッド + スリッページ JPY コスト (片道)"""
    pv = compute_pip_value_jpy(instrument, lots, mid_price)
    spread_pips = SPREAD_PIPS[instrument]
    slip_entry = SLIPPAGE_PIPS_ENTRY
    return pv * (spread_pips + slip_entry)


def compute_swap_jpy_per_day(instrument: str, lots: float, direction: int, mid_price: float) -> float:
    """1 日当たりのスワップ JPY (direction +1 = ロング)"""
    units = lots * LOT_SIZE
    notional_quote = units * mid_price  # 概算 notional in quote currency
    notional_jpy = notional_quote * get_quote_to_jpy(instrument, mid_price)
    # USD/JPY なら quote=JPY なので、notional_quote が JPY
    # 他は: notional_quote → JPY 変換は get_quote_to_jpy で

    # 通貨ペアの quote currency が "それ自体" の場合、notional_jpy 計算が二重になる懸念
    # ここでは USD_JPY の場合 notional_quote が既に JPY なので分けて扱う
    if instrument.endswith("_JPY"):
        notional_jpy = units * mid_price  # = JPY 額面
    else:
        # quote が USD/CHF/CAD などの場合、quote 額面 -> JPY
        notional_quote_amount = units * mid_price
        notional_jpy = notional_quote_amount * get_quote_to_jpy(instrument, mid_price)

    long_swap = LONG_SWAP_PCT[instrument] / 100.0  # 年率
    if direction > 0:
        annual_swap = long_swap  # ロング側
    else:
        annual_swap = -long_swap - (SHORT_SWAP_PENALTY / 100.0)  # ショートはペナルティ追加
    daily_swap_jpy = notional_jpy * annual_swap / 365.0
    return daily_swap_jpy


def simulate(data: dict[str, pd.DataFrame], pairs_to_trade: list[tuple[str, str]],
             start: pd.Timestamp, end: pd.Timestamp,
             apply_kill_switch: bool = True,
             reeval_every_days: int = COINT_REEVAL_INTERVAL_DAYS,
             coint_window_days: int = COINT_TEST_WINDOW_DAYS,
             coint_pval_threshold: float = None,
             verbose: bool = False) -> dict:
    """シミュレーション本体

    coint_pval_threshold: 動的指定 (None なら module 定数を使用)
    """
    if coint_pval_threshold is None:
        coint_pval_threshold = COINT_PVAL_THRESHOLD
    """戦略シミュレーション

    動作:
    - 共通インデックスを生成
    - 各 reeval_every_days で 過去 coint_window_days 分の cointegration テスト
    - p<0.05 のペアのみ取引対象 (β も同時に推定)
    - 各バーで z-score を計算 → entry/exit/stop 判定
    - キルスイッチ: 日次 -5% で停止 / 月次 -10% で停止

    Returns: dict with 'trades_df', 'equity_curve', 'monthly_returns', 'stats'
    """
    # 共通インデックス
    base_idx = data[INSTRUMENTS[0]].loc[start:end].index
    capital_jpy = INITIAL_CAPITAL_JPY
    equity_history = []
    open_positions: list[Position] = []
    trades_log = []

    # キルスイッチ状態
    halted_until_date = None
    daily_pnl_tracker = {}  # date -> pnl
    monthly_pnl_tracker = {}  # YYYY-MM -> pnl
    halted_today = False

    # ペアの状態: 各 pair に対する current beta / 取引可能か / 最後の coint テスト結果
    pair_state = {pair: {"is_active": False, "beta": None, "last_eval": None, "pvalue": None}
                  for pair in pairs_to_trade}

    last_reeval_idx = -reeval_every_days  # 即時初回評価
    bar_count = 0
    debug_stats = {"active_pair_bars": 0, "z_attempts": 0, "z_over_entry": 0, "active_pair_count_max": 0,
                   "entry_block_force_close": 0, "entry_block_halt": 0, "entry_block_full": 0,
                   "entry_block_inactive": 0, "entry_block_dup": 0, "entry_block_no_data": 0}

    for i, ts in enumerate(base_idx):
        bar_count += 1

        # ----- 共和分再評価 -----
        if i - last_reeval_idx >= reeval_every_days:
            window_end = ts
            window_start = ts - pd.Timedelta(days=coint_window_days)
            # データ範囲外: スキップ (まだ十分な過去データがない)
            if window_start < base_idx[0]:
                last_reeval_idx = i
                equity_history.append({"timestamp": ts, "equity": capital_jpy, "open_positions": len(open_positions)})
                continue
            for pair_a, pair_b in pairs_to_trade:
                sa = data[pair_a].loc[window_start:window_end, "close"]
                sb = data[pair_b].loc[window_start:window_end, "close"]
                if len(sa) < 30:
                    continue
                res = coint_test(sa, sb)
                pval = res["pvalue"]
                pair_state[(pair_a, pair_b)]["pvalue"] = pval
                pair_state[(pair_a, pair_b)]["last_eval"] = ts
                if not np.isnan(pval) and pval < coint_pval_threshold:
                    pair_state[(pair_a, pair_b)]["is_active"] = True
                    pair_state[(pair_a, pair_b)]["beta"] = res["beta"]
                else:
                    pair_state[(pair_a, pair_b)]["is_active"] = False
            last_reeval_idx = i

        # ----- 日次・月次キルスイッチチェック -----
        date_key = ts.date()
        month_key = ts.strftime("%Y-%m")
        equity_pct_today = (capital_jpy - INITIAL_CAPITAL_JPY) / INITIAL_CAPITAL_JPY * 100
        # 日次 / 月次の損益累計
        if date_key not in daily_pnl_tracker:
            daily_pnl_tracker[date_key] = 0.0
        if month_key not in monthly_pnl_tracker:
            monthly_pnl_tracker[month_key] = 0.0

        # 停止チェック
        force_close_all = False
        if apply_kill_switch:
            daily_pct = daily_pnl_tracker[date_key] / INITIAL_CAPITAL_JPY * 100
            month_pct = monthly_pnl_tracker[month_key] / INITIAL_CAPITAL_JPY * 100
            if daily_pct <= DAILY_LOSS_HARD_STOP_PCT or month_pct <= MONTHLY_LOSS_LIMIT_PCT:
                force_close_all = True
                halted_until_date = (ts + pd.Timedelta(days=1)).date()

        # ----- 既存ポジションの更新・クローズ判定 -----
        new_open_positions = []
        for pos in open_positions:
            pos.bars_held += 1

            # 現在価格
            price_a_close = data[pos.pair_a].loc[ts, "close"]
            price_b_close = data[pos.pair_b].loc[ts, "close"]

            # スワップ累積
            swap_a = compute_swap_jpy_per_day(pos.pair_a, pos.volume_lots_a, pos.direction, price_a_close)
            swap_b = compute_swap_jpy_per_day(pos.pair_b, pos.volume_lots_b, -pos.direction, price_b_close)
            pos.swap_accumulated_jpy += (swap_a + swap_b)

            # 現在 z-score を計算 (spread = A - β*B), 営業日ベースで iloc を使う
            full_idx_a = data[pos.pair_a].index
            cur_pos = full_idx_a.get_loc(ts)
            start_pos = max(0, cur_pos - ZSCORE_LOOKBACK - 5)
            sa = data[pos.pair_a].iloc[start_pos:cur_pos + 1]["close"]
            sb = data[pos.pair_b].iloc[start_pos:cur_pos + 1]["close"]
            spread = sa - pos.beta * sb
            if len(spread) < ZSCORE_LOOKBACK:
                new_open_positions.append(pos)
                continue
            z = compute_zscore(spread, ZSCORE_LOOKBACK).iloc[-1]

            should_exit = False
            exit_reason = None
            if abs(z) <= EXIT_Z:
                should_exit = True
                exit_reason = "mean_reversion"
            elif abs(z) >= STOP_Z:
                should_exit = True
                exit_reason = "stop_loss"
            elif pos.bars_held >= MAX_HOLD_DAYS:
                should_exit = True
                exit_reason = "time_stop"
            elif force_close_all:
                should_exit = True
                exit_reason = "kill_switch"

            if should_exit:
                # PnL 計算 (price change × units × pip_value)
                # ロング側 A: direction=+1 なら買い → exit-entry
                pnl_a_quote = (price_a_close - pos.open_price_a) * pos.direction * pos.volume_lots_a * LOT_SIZE
                pnl_b_quote = (price_b_close - pos.open_price_b) * (-pos.direction) * pos.volume_lots_b * LOT_SIZE
                # JPY 換算
                pnl_a_jpy = pnl_a_quote * get_quote_to_jpy(pos.pair_a, price_a_close)
                pnl_b_jpy = pnl_b_quote * get_quote_to_jpy(pos.pair_b, price_b_close)
                # スプレッド + スリッページ コスト (片道、約定時/決済時の合計を 2 回控除)
                cost_a = compute_spread_cost_jpy(pos.pair_a, pos.volume_lots_a, price_a_close) * 2  # entry + exit
                cost_b = compute_spread_cost_jpy(pos.pair_b, pos.volume_lots_b, price_b_close) * 2
                total_pnl_jpy = pnl_a_jpy + pnl_b_jpy + pos.swap_accumulated_jpy - cost_a - cost_b

                capital_jpy += total_pnl_jpy
                daily_pnl_tracker[date_key] += total_pnl_jpy
                monthly_pnl_tracker[month_key] += total_pnl_jpy

                trades_log.append({
                    "pair_a": pos.pair_a, "pair_b": pos.pair_b,
                    "direction": pos.direction,
                    "open_time": pos.open_time, "close_time": ts,
                    "bars_held": pos.bars_held,
                    "open_price_a": pos.open_price_a, "close_price_a": price_a_close,
                    "open_price_b": pos.open_price_b, "close_price_b": price_b_close,
                    "beta": pos.beta,
                    "entry_z": pos.entry_z, "exit_z": z,
                    "pnl_a_jpy": pnl_a_jpy, "pnl_b_jpy": pnl_b_jpy,
                    "swap_jpy": pos.swap_accumulated_jpy,
                    "cost_a_jpy": cost_a, "cost_b_jpy": cost_b,
                    "total_pnl_jpy": total_pnl_jpy,
                    "exit_reason": exit_reason,
                    "capital_after": capital_jpy,
                })
            else:
                new_open_positions.append(pos)
        open_positions = new_open_positions

        # 統計: active 状態のペア数
        active_count = sum(1 for v in pair_state.values() if v["is_active"])
        if active_count > 0:
            debug_stats["active_pair_bars"] += 1
            debug_stats["active_pair_count_max"] = max(debug_stats["active_pair_count_max"], active_count)

        # ----- 新規エントリー -----
        if force_close_all:
            debug_stats["entry_block_force_close"] += 1
        elif halted_until_date is not None and date_key < halted_until_date:
            debug_stats["entry_block_halt"] += 1
        elif len(open_positions) >= 3:
            debug_stats["entry_block_full"] += 1
        else:
            for pair_a, pair_b in pairs_to_trade:
                if not pair_state[(pair_a, pair_b)]["is_active"]:
                    debug_stats["entry_block_inactive"] += 1
                    continue
                # 同じペアが既にオープン中ならスキップ
                if any(p.pair_a == pair_a and p.pair_b == pair_b for p in open_positions):
                    debug_stats["entry_block_dup"] += 1
                    continue
                beta = pair_state[(pair_a, pair_b)]["beta"]
                # 直近の spread と z 計算 (営業日 iloc ベース)
                full_idx_a = data[pair_a].index
                cur_pos = full_idx_a.get_loc(ts)
                start_pos = max(0, cur_pos - ZSCORE_LOOKBACK - 5)
                sa = data[pair_a].iloc[start_pos:cur_pos + 1]["close"]
                sb = data[pair_b].iloc[start_pos:cur_pos + 1]["close"]
                if len(sa) < ZSCORE_LOOKBACK:
                    debug_stats["entry_block_no_data"] += 1
                    continue
                spread = sa - beta * sb
                z = compute_zscore(spread, ZSCORE_LOOKBACK).iloc[-1]
                if np.isnan(z):
                    continue
                debug_stats["z_attempts"] += 1

                direction = 0
                if z >= ENTRY_Z:
                    direction = -1  # spread が高すぎる → short spread = short A, long B
                elif z <= -ENTRY_Z:
                    direction = +1  # spread が低すぎる → long spread = long A, short B

                if direction == 0:
                    continue
                debug_stats["z_over_entry"] += 1

                # β 比でロット調整 (notional 中立)
                vol_a = TRADE_VOLUME_LOTS
                vol_b = TRADE_VOLUME_LOTS * abs(beta)
                price_a = data[pair_a].loc[ts, "close"]
                price_b = data[pair_b].loc[ts, "close"]

                pos = Position(
                    pair_a=pair_a, pair_b=pair_b,
                    direction=direction,
                    beta=beta,
                    open_time=ts,
                    open_price_a=price_a, open_price_b=price_b,
                    volume_lots_a=vol_a, volume_lots_b=vol_b,
                    entry_z=z,
                )
                open_positions.append(pos)
                if len(open_positions) >= 3:
                    break

        equity_history.append({"timestamp": ts, "equity": capital_jpy, "open_positions": len(open_positions)})

    # 最終クローズ
    for pos in open_positions:
        ts = base_idx[-1]
        price_a = data[pos.pair_a].loc[ts, "close"]
        price_b = data[pos.pair_b].loc[ts, "close"]
        pnl_a_quote = (price_a - pos.open_price_a) * pos.direction * pos.volume_lots_a * LOT_SIZE
        pnl_b_quote = (price_b - pos.open_price_b) * (-pos.direction) * pos.volume_lots_b * LOT_SIZE
        pnl_a_jpy = pnl_a_quote * get_quote_to_jpy(pos.pair_a, price_a)
        pnl_b_jpy = pnl_b_quote * get_quote_to_jpy(pos.pair_b, price_b)
        cost_a = compute_spread_cost_jpy(pos.pair_a, pos.volume_lots_a, price_a) * 2
        cost_b = compute_spread_cost_jpy(pos.pair_b, pos.volume_lots_b, price_b) * 2
        total_pnl_jpy = pnl_a_jpy + pnl_b_jpy + pos.swap_accumulated_jpy - cost_a - cost_b
        capital_jpy += total_pnl_jpy
        trades_log.append({
            "pair_a": pos.pair_a, "pair_b": pos.pair_b,
            "direction": pos.direction,
            "open_time": pos.open_time, "close_time": ts,
            "bars_held": pos.bars_held,
            "open_price_a": pos.open_price_a, "close_price_a": price_a,
            "open_price_b": pos.open_price_b, "close_price_b": price_b,
            "beta": pos.beta,
            "entry_z": pos.entry_z, "exit_z": np.nan,
            "pnl_a_jpy": pnl_a_jpy, "pnl_b_jpy": pnl_b_jpy,
            "swap_jpy": pos.swap_accumulated_jpy,
            "cost_a_jpy": cost_a, "cost_b_jpy": cost_b,
            "total_pnl_jpy": total_pnl_jpy,
            "exit_reason": "final_close",
            "capital_after": capital_jpy,
        })

    trades_df = pd.DataFrame(trades_log)
    if len(equity_history) > 0:
        equity_df = pd.DataFrame(equity_history).set_index("timestamp")
    else:
        equity_df = pd.DataFrame(columns=["equity", "open_positions"])
        equity_df.index.name = "timestamp"

    # 月次集計
    if len(trades_df) > 0:
        trades_df["close_month"] = pd.to_datetime(trades_df["close_time"]).dt.to_period("M").astype(str)
        monthly = trades_df.groupby("close_month").agg(
            n_trades=("total_pnl_jpy", "count"),
            sum_pnl_jpy=("total_pnl_jpy", "sum"),
            win_rate=("total_pnl_jpy", lambda s: (s > 0).mean()),
        )
    else:
        monthly = pd.DataFrame(columns=["n_trades", "sum_pnl_jpy", "win_rate"])

    return {
        "trades_df": trades_df,
        "equity_df": equity_df,
        "monthly": monthly,
        "final_capital": capital_jpy,
        "debug_stats": debug_stats,
    }


# =================================================================
# 統計計算
# =================================================================


def compute_stats(trades_df: pd.DataFrame, equity_df: pd.DataFrame,
                  initial_capital: float = INITIAL_CAPITAL_JPY) -> dict:
    """BT 結果統計: PF, Sharpe, Sortino, MaxDD, Win Rate, Deflated Sharpe"""
    if len(trades_df) == 0:
        return {
            "n_trades": 0, "pf": np.nan, "sharpe": np.nan, "sortino": np.nan,
            "maxdd_pct": np.nan, "win_rate": np.nan, "total_pnl_jpy": 0.0,
            "deflated_sharpe": np.nan,
        }

    pnl = trades_df["total_pnl_jpy"]
    wins = pnl[pnl > 0].sum()
    losses = -pnl[pnl < 0].sum()
    pf = wins / losses if losses > 0 else np.inf

    # 日次リターン (equity_df の前日差)
    equity_df = equity_df.copy()
    equity_df["daily_ret"] = equity_df["equity"].pct_change()
    daily_ret = equity_df["daily_ret"].dropna()
    if daily_ret.std() > 0:
        sharpe_annual = daily_ret.mean() / daily_ret.std() * np.sqrt(252)
    else:
        sharpe_annual = 0.0
    downside = daily_ret[daily_ret < 0]
    sortino = daily_ret.mean() / downside.std() * np.sqrt(252) if len(downside) > 0 and downside.std() > 0 else np.nan

    # MaxDD
    equity_df["roll_max"] = equity_df["equity"].cummax()
    equity_df["dd"] = (equity_df["equity"] - equity_df["roll_max"]) / equity_df["roll_max"]
    maxdd_pct = equity_df["dd"].min() * 100

    win_rate = (pnl > 0).mean()

    # 最長連敗
    streak = 0
    max_streak = 0
    for v in pnl:
        if v < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    # Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014)
    # DSR = ((SR - SR_expected) / σ_SR) × √(N-1)
    # SR_expected = √(2 ln N) × σ_SR (multi-test correction)
    N = len(trades_df)
    SR = sharpe_annual / np.sqrt(252)  # 日次 Sharpe に戻す
    sigma_SR = np.sqrt((1 - daily_ret.skew()*SR + (daily_ret.kurtosis()-1)/4 * SR**2) / (len(daily_ret)-1)) if len(daily_ret) > 10 else np.nan
    n_trials = 50  # 試行回数想定 (パラメータ感度 + WFA 多重)
    SR_expected = sigma_SR * np.sqrt(2 * np.log(n_trials)) if not np.isnan(sigma_SR) else np.nan
    # Deflated Sharpe : 元の sharpe_annual と比較
    dsr_z = (SR - SR_expected) / sigma_SR if not np.isnan(sigma_SR) and sigma_SR > 0 else np.nan

    return {
        "n_trades": int(N),
        "pf": float(pf),
        "sharpe": float(sharpe_annual),
        "sortino": float(sortino) if not np.isnan(sortino) else None,
        "maxdd_pct": float(maxdd_pct),
        "win_rate": float(win_rate),
        "total_pnl_jpy": float(pnl.sum()),
        "max_loss_streak": int(max_streak),
        "deflated_sharpe_z": float(dsr_z) if not np.isnan(dsr_z) else None,
        "deflated_sharpe_pass": bool(dsr_z > 0) if not np.isnan(dsr_z) else None,
    }


# =================================================================
# Walk-Forward Analysis
# =================================================================


def walk_forward(data: dict[str, pd.DataFrame], pairs_to_trade: list[tuple[str, str]]) -> list[dict]:
    """12 ヶ月学習 / 3 ヶ月運用、step 1 ヶ月の WFA"""
    base_idx = data[INSTRUMENTS[0]].index
    start = base_idx[0]
    end = base_idx[-1]

    train_td = pd.Timedelta(days=WFA_TRAIN_DAYS)
    test_td = pd.Timedelta(days=WFA_TEST_DAYS)
    step_td = pd.Timedelta(days=30)

    results = []
    cur = start + train_td
    window_idx = 0
    while cur + test_td <= end:
        test_start = cur
        test_end = cur + test_td
        # train period: cur - train_td -> cur (cointegration の信頼度確認のみ)
        train_start = cur - train_td
        # train で coint 行列を計算 (情報用)
        sim = simulate(data, pairs_to_trade, test_start, test_end, apply_kill_switch=True)
        stats = compute_stats(sim["trades_df"], sim["equity_df"], INITIAL_CAPITAL_JPY)
        stats["window_idx"] = window_idx
        stats["test_start"] = test_start
        stats["test_end"] = test_end
        results.append(stats)
        window_idx += 1
        cur += step_td

    return results


# =================================================================
# Black Swan ストレステスト
# =================================================================


def black_swan_stress_test(data: dict[str, pd.DataFrame], pairs_to_trade: list[tuple[str, str]]) -> list[dict]:
    """主要 Black Swan イベント前後の挙動 (キルスイッチ動作確認)"""
    base_idx = data[INSTRUMENTS[0]].index
    data_start = base_idx[0]

    # 利用可能な範囲内の事象
    events = [
        ("2020 COVID 暴落", "2020-02-15", "2020-04-30"),
        ("2022 後半 GBP 危機", "2022-09-01", "2022-12-31"),
        ("2023 銀行危機", "2023-03-01", "2023-04-30"),
        ("2024-07 円介入", "2024-07-01", "2024-08-30"),
        ("2024-08 キャリー巻戻し", "2024-08-01", "2024-08-31"),
    ]

    results = []
    for name, e_start, e_end in events:
        e_start_ts = pd.Timestamp(e_start, tz="UTC")
        e_end_ts = pd.Timestamp(e_end, tz="UTC")
        if e_end_ts < data_start:
            results.append({"event": name, "skipped": True, "reason": "out of data range"})
            continue
        if e_start_ts < data_start:
            e_start_ts = data_start

        sim = simulate(data, pairs_to_trade, e_start_ts, e_end_ts, apply_kill_switch=True)
        stats = compute_stats(sim["trades_df"], sim["equity_df"], INITIAL_CAPITAL_JPY)
        stats["event"] = name
        stats["start"] = str(e_start_ts.date())
        stats["end"] = str(e_end_ts.date())
        # キルスイッチ作動の有無を trade log の exit_reason から確認
        if len(sim["trades_df"]) > 0:
            stats["kill_switch_triggered"] = (sim["trades_df"]["exit_reason"] == "kill_switch").any()
            stats["stop_loss_count"] = (sim["trades_df"]["exit_reason"] == "stop_loss").sum()
        else:
            stats["kill_switch_triggered"] = False
            stats["stop_loss_count"] = 0
        results.append(stats)

    return results


# =================================================================
# パラメータ感度
# =================================================================


def parameter_sensitivity(data: dict[str, pd.DataFrame], pairs_to_trade: list[tuple[str, str]]) -> list[dict]:
    """主要パラメータ ±20% の感度分析"""
    global ENTRY_Z, EXIT_Z, ZSCORE_LOOKBACK, COINT_PVAL_THRESHOLD

    original = {
        "entry_z": ENTRY_Z, "exit_z": EXIT_Z,
        "lookback": ZSCORE_LOOKBACK, "pval": COINT_PVAL_THRESHOLD,
    }
    base_idx = data[INSTRUMENTS[0]].index
    start = base_idx[0]
    end = base_idx[-1]

    scenarios = [
        ("baseline", 2.0, 0.5, 60, 0.05),
        ("entry_z_high", 2.4, 0.5, 60, 0.05),
        ("entry_z_low", 1.6, 0.5, 60, 0.05),
        ("exit_z_high", 2.0, 0.6, 60, 0.05),
        ("exit_z_low", 2.0, 0.4, 60, 0.05),
        ("lookback_high", 2.0, 0.5, 72, 0.05),
        ("lookback_low", 2.0, 0.5, 48, 0.05),
        ("pval_strict", 2.0, 0.5, 60, 0.025),
        ("pval_loose", 2.0, 0.5, 60, 0.10),
    ]

    results = []
    for name, ez, xz, lb, pv in scenarios:
        ENTRY_Z = ez
        EXIT_Z = xz
        ZSCORE_LOOKBACK = lb
        COINT_PVAL_THRESHOLD = pv
        sim = simulate(data, pairs_to_trade, start, end, apply_kill_switch=True)
        stats = compute_stats(sim["trades_df"], sim["equity_df"], INITIAL_CAPITAL_JPY)
        stats["scenario"] = name
        stats["entry_z"] = ez
        stats["exit_z"] = xz
        stats["lookback"] = lb
        stats["pval"] = pv
        results.append(stats)

    # 元に戻す
    ENTRY_Z = original["entry_z"]
    EXIT_Z = original["exit_z"]
    ZSCORE_LOOKBACK = original["lookback"]
    COINT_PVAL_THRESHOLD = original["pval"]

    return results


# =================================================================
# Main
# =================================================================


def main():
    print("=" * 60)
    print("Phase 2 BT: 候補 #12 Cointegration Pairs Trading")
    print("=" * 60)

    print("\n[1/6] データロード ...")
    data = load_pair_data()
    base_idx = data[INSTRUMENTS[0]].index
    print(f"  期間: {base_idx[0].date()} -> {base_idx[-1].date()} ({len(base_idx)}日)")

    # IS / OOS 分割 (70/30)
    split_idx = int(len(base_idx) * 0.7)
    is_end = base_idx[split_idx]
    oos_start = base_idx[split_idx + 1]
    print(f"  IS:  {base_idx[0].date()} -> {is_end.date()} ({split_idx}日)")
    print(f"  OOS: {oos_start.date()} -> {base_idx[-1].date()} ({len(base_idx)-split_idx-1}日)")

    print("\n[2/6] ペア選定 cointegration 行列計算 (フル期間) ...")
    pairs_df_full = cointegration_matrix(data, base_idx[0], base_idx[-1])
    pairs_df_full = pairs_df_full.sort_values("pvalue")
    print(pairs_df_full.head(20).to_string())

    # 取引対象ペアを動的選定:
    # 全 21 ペア組合せを取引対象にし、ローリング coint で動的フィルタ (本来の戦略動作)
    pairs_to_trade = []
    insts = list(data.keys())
    for i, a in enumerate(insts):
        for j, b in enumerate(insts):
            if i < j:
                # EUR_CHF などの構造変化ペアを除外 (SNB 後不安定)
                if {a, b} == {"USD_CHF", "EUR_USD"}:
                    continue
                pairs_to_trade.append((a, b))
    print(f"  取引対象ペア (動的フィルタ前): {len(pairs_to_trade)} 組合せ")
    print(f"  {pairs_to_trade}")

    print("\n[3/6] フル期間シミュレーション ...")
    sim_full = simulate(data, pairs_to_trade, base_idx[0], base_idx[-1], apply_kill_switch=True)
    stats_full = compute_stats(sim_full["trades_df"], sim_full["equity_df"], INITIAL_CAPITAL_JPY)
    stats_full["period"] = "FULL"
    print(f"  Total trades: {stats_full['n_trades']}")
    print(f"  debug: {sim_full['debug_stats']}")
    if stats_full['n_trades'] > 0:
        print(f"  PF: {stats_full['pf']:.3f}")
        print(f"  Sharpe: {stats_full['sharpe']:.3f}")
        print(f"  MaxDD: {stats_full['maxdd_pct']:.2f}%")
    print(f"  Final capital: {sim_full['final_capital']:,.0f} JPY")
    print(f"  Total PnL: {stats_full['total_pnl_jpy']:,.0f} JPY")

    print("\n[3.5/6] IS / OOS 個別実行 ...")
    sim_is = simulate(data, pairs_to_trade, base_idx[0], is_end, apply_kill_switch=True)
    stats_is = compute_stats(sim_is["trades_df"], sim_is["equity_df"], INITIAL_CAPITAL_JPY)
    stats_is["period"] = "IS"
    print(f"  IS:  trades={stats_is['n_trades']}, PF={stats_is['pf']:.3f}, Sharpe={stats_is['sharpe']:.3f}")
    sim_oos = simulate(data, pairs_to_trade, oos_start, base_idx[-1], apply_kill_switch=True)
    stats_oos = compute_stats(sim_oos["trades_df"], sim_oos["equity_df"], INITIAL_CAPITAL_JPY)
    stats_oos["period"] = "OOS"
    print(f"  OOS: trades={stats_oos['n_trades']}, PF={stats_oos['pf']:.3f}, Sharpe={stats_oos['sharpe']:.3f}")

    print("\n[4/6] Walk-Forward Analysis ...")
    wfa_results = walk_forward(data, pairs_to_trade)
    wfa_df = pd.DataFrame(wfa_results)
    print(f"  Windows: {len(wfa_df)}")
    if len(wfa_df) > 0:
        wfa_df_valid = wfa_df[wfa_df["n_trades"] > 0]
        if len(wfa_df_valid) > 0:
            print(f"  Mean PF: {wfa_df_valid['pf'].mean():.3f}")
            print(f"  Mean Sharpe: {wfa_df_valid['sharpe'].mean():.3f}")
            print(f"  Win windows (PF>=1.3): {(wfa_df_valid['pf'] >= 1.3).sum()} / {len(wfa_df_valid)}")

    print("\n[5/6] Black Swan ストレステスト ...")
    stress_results = black_swan_stress_test(data, pairs_to_trade)
    stress_df = pd.DataFrame(stress_results)
    print(stress_df[["event", "n_trades", "pf", "total_pnl_jpy", "maxdd_pct", "kill_switch_triggered"]].to_string() if len(stress_df) > 0 else "(no events)")

    print("\n[6/6] パラメータ感度分析 ...")
    sens_results = parameter_sensitivity(data, pairs_to_trade)
    sens_df = pd.DataFrame(sens_results)
    print(sens_df[["scenario", "n_trades", "pf", "sharpe", "maxdd_pct"]].to_string())

    # ===== ファイル保存 =====
    print("\n--- 出力保存 ---")

    out_trades = DATA_DIR / "_phase2_bt_12_cointegration_trades.csv"
    sim_full["trades_df"].to_csv(out_trades, index=False)
    print(f"  trades: {out_trades}")

    out_monthly = DATA_DIR / "_phase2_bt_12_cointegration_monthly.csv"
    sim_full["monthly"].to_csv(out_monthly)
    print(f"  monthly: {out_monthly}")

    out_stress = DATA_DIR / "_phase2_bt_12_cointegration_stress.csv"
    stress_df.to_csv(out_stress, index=False)
    print(f"  stress: {out_stress}")

    out_pairs = DATA_DIR / "_phase2_bt_12_cointegration_pairs.csv"
    pairs_df_full.to_csv(out_pairs, index=False)
    print(f"  pairs (coint matrix): {out_pairs}")

    out_sens = DATA_DIR / "_phase2_bt_12_cointegration_sensitivity.csv"
    sens_df.to_csv(out_sens, index=False)
    print(f"  sensitivity: {out_sens}")

    out_wfa = DATA_DIR / "_phase2_bt_12_cointegration_wfa.csv"
    if len(wfa_df) > 0:
        wfa_df.to_csv(out_wfa, index=False)
        print(f"  wfa: {out_wfa}")

    # ===== 全結果集約 =====
    import json
    summary = {
        "full": stats_full,
        "is": stats_is,
        "oos": stats_oos,
        "wfa": wfa_results,
        "stress": stress_results,
        "sensitivity": sens_results,
        "pairs_to_trade": [list(p) for p in pairs_to_trade],
        "data_period": {"start": str(base_idx[0].date()), "end": str(base_idx[-1].date()), "bars": len(base_idx)},
    }
    out_json = DATA_DIR / "_phase2_bt_12_cointegration_summary.json"
    with open(out_json, "w", encoding="utf-8") as f:
        # NaN 安全に
        def _safe(o):
            if isinstance(o, float) and (np.isnan(o) or np.isinf(o)):
                return None
            if isinstance(o, (pd.Timestamp,)):
                return str(o)
            return o
        json.dump(summary, f, indent=2, default=lambda o: _safe(o) if _safe(o) is not None else str(o), ensure_ascii=False)
    print(f"  summary json: {out_json}")

    print("\n完了。BT スクリプト終了。")


if __name__ == "__main__":
    main()
