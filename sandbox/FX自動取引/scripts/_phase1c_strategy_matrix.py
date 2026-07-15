"""Phase 1X-Probe Job-A+B: 戦略マトリックスBT (#1+#2+#4)

#1 USD_JPY 撤退妥当性: 既存戦略以外で勝てるか
#2 MTFPullback × USD_JPY 相性: 別戦略を当てた感度
#4 A案 Regime Gating: ADX>25→Breakout / <20→Reversion で 5/6 相場を取れるか

3ペア × 5戦略 × 期間2y のPF/N グリッド。

戦略:
- baseline: MTFPullback (RSI Pullback + ADX)
- cguard: MTFPullback + slope guard (C案 v2)
- donchian: 20本Donchianブレイクアウト (ADX>=25)
- bollinger: BB逆張り (ADX<=20)
- regime: ADX>25 → Donchian、<20 → MTFPullback、中間 No-trade
"""
from __future__ import annotations

import io
import json
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

import numpy as np
import pandas as pd
import pandas_ta as ta
from backtesting import Strategy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.backtester import BacktestEngine, calculate_spread  # noqa: E402

# Gate スクリプトから既存戦略を re-use
import importlib.util  # noqa: E402
_gate_spec = importlib.util.spec_from_file_location(
    "_phase1c_gate", Path(__file__).parent / "_phase1c_gate_validation.py",
)
_gate_mod = importlib.util.module_from_spec(_gate_spec)
_gate_spec.loader.exec_module(_gate_mod)
RsiPullbackADXBT = _gate_mod.RsiPullbackADXBT
RsiPullbackADXBT_CGuard = _gate_mod.RsiPullbackADXBT_CGuard
load_mt5_csv = _gate_mod.load_mt5_csv

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("strategy_matrix")
log.setLevel(logging.INFO)


# ============================================================
# 共通: ADX計算ヘルパー
# ============================================================
def _adx_only(h, l, c, length=14):
    r = ta.adx(pd.Series(h), pd.Series(l), pd.Series(c), length=length)
    if r is None:
        return pd.Series([np.nan] * len(c))
    col = f"ADX_{length}"
    return r[col] if col in r.columns else pd.Series([np.nan] * len(c))


# ============================================================
# DonchianBreakout: ADX>=25 で20本ブレイクアウト
# ============================================================
class DonchianBreakout(Strategy):
    n_channel = 20
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0
    adx_period = 14
    adx_threshold = 25.0

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        n = self.n_channel
        self.high_n = self.I(
            lambda h: pd.Series(h).rolling(n).max().shift(1).values,
            high, name="HighN",
        )
        self.low_n = self.I(
            lambda l: pd.Series(l).rolling(n).min().shift(1).values,
            low, name="LowN",
        )
        self.atr = self.I(ta.atr, high, low, close, length=self.atr_period, name="ATR")
        adx_len = self.adx_period
        self.adx = self.I(
            lambda h, l, c: _adx_only(h, l, c, length=adx_len),
            high, low, close, name="ADX",
        )

    def next(self):
        if (np.isnan(self.high_n[-1]) or np.isnan(self.low_n[-1])
            or np.isnan(self.atr[-1]) or np.isnan(self.adx[-1])):
            return
        if self.atr[-1] == 0 or self.position:
            return
        if self.adx[-1] < self.adx_threshold:
            return

        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        if price > self.high_n[-1]:
            self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
        elif price < self.low_n[-1]:
            self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)


# ============================================================
# BollingerReversal: ADX<=20 で BB±2σ タッチ逆張り
# ============================================================
class BollingerReversalBT(Strategy):
    bb_length = 20
    bb_std = 2.0
    atr_period = 14
    atr_mult = 1.5
    rr = 1.5
    adx_period = 14
    adx_max = 20.0  # ADX高すぎたらやらない

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        bb_len = self.bb_length
        bb_std = self.bb_std

        def _bb_upper(c):
            s = pd.Series(c)
            return (s.rolling(bb_len).mean() + bb_std * s.rolling(bb_len).std()).values

        def _bb_lower(c):
            s = pd.Series(c)
            return (s.rolling(bb_len).mean() - bb_std * s.rolling(bb_len).std()).values

        def _bb_mid(c):
            return pd.Series(c).rolling(bb_len).mean().values

        self.bb_upper = self.I(_bb_upper, close, name="BBU")
        self.bb_lower = self.I(_bb_lower, close, name="BBL")
        self.bb_mid = self.I(_bb_mid, close, name="BBM")
        self.atr = self.I(ta.atr, high, low, close, length=self.atr_period, name="ATR")
        adx_len = self.adx_period
        self.adx = self.I(
            lambda h, l, c: _adx_only(h, l, c, length=adx_len),
            high, low, close, name="ADX",
        )

    def next(self):
        if (np.isnan(self.bb_upper[-1]) or np.isnan(self.atr[-1])
            or np.isnan(self.adx[-1])):
            return
        if self.atr[-1] == 0 or self.position:
            return
        if self.adx[-1] > self.adx_max:
            return  # トレンド時は逆張り危険

        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        if price >= self.bb_upper[-1]:
            self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)
        elif price <= self.bb_lower[-1]:
            self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)


# ============================================================
# RegimeGating: ADX>=25 → Donchian、<=20 → MTFPullback、中間=No-trade
# ============================================================
class RegimeGating(Strategy):
    # MTFPullback パラメータ
    trend_ma = 200
    rsi_period = 14
    rsi_oversold = 35
    rsi_overbought = 65
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0
    adx_period = 14
    # ADX閾値
    adx_low = 20.0   # 以下 → Reversion
    adx_high = 25.0  # 以上 → Breakout
    # Donchian パラメータ
    n_channel = 20

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        self.ma_trend = self.I(ta.sma, close, length=self.trend_ma, name="MA_trend")
        self.rsi = self.I(ta.rsi, close, length=self.rsi_period, name="RSI")
        self.atr = self.I(ta.atr, high, low, close, length=self.atr_period, name="ATR")
        adx_len = self.adx_period
        self.adx = self.I(
            lambda h, l, c: _adx_only(h, l, c, length=adx_len),
            high, low, close, name="ADX",
        )
        n = self.n_channel
        self.high_n = self.I(
            lambda h: pd.Series(h).rolling(n).max().shift(1).values,
            high, name="HighN",
        )
        self.low_n = self.I(
            lambda l: pd.Series(l).rolling(n).min().shift(1).values,
            low, name="LowN",
        )

    def next(self):
        if (np.isnan(self.ma_trend[-1]) or np.isnan(self.rsi[-1])
            or np.isnan(self.atr[-1]) or np.isnan(self.adx[-1])
            or np.isnan(self.high_n[-1]) or np.isnan(self.low_n[-1])):
            return
        if self.atr[-1] == 0 or self.position:
            return

        adx = self.adx[-1]
        # No-trade 中間帯
        if self.adx_low < adx < self.adx_high:
            return

        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        if adx >= self.adx_high:
            # Breakout モード
            if price > self.high_n[-1]:
                self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
            elif price < self.low_n[-1]:
                self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)
        else:  # adx <= adx_low
            # MTFPullback モード
            if price > self.ma_trend[-1] and self.rsi[-1] < self.rsi_oversold:
                self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
            elif price < self.ma_trend[-1] and self.rsi[-1] > self.rsi_overbought:
                self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)


# ============================================================
# 設定
# ============================================================
PAIRS = {
    "USD_JPY": ("mt5_USD_JPY_M15_2y.csv", 20.0),
    "EUR_USD": ("mt5_EUR_USD_M15_2y.csv", 25.0),
    "GBP_JPY": ("mt5_GBP_JPY_M15_2y.csv", 25.0),
}

STRATEGIES = [
    ("baseline",  RsiPullbackADXBT,         {}),
    ("cguard",    RsiPullbackADXBT_CGuard,  {}),
    ("donchian",  DonchianBreakout,         {}),
    ("bb_revers", BollingerReversalBT,      {}),
    ("regime",    RegimeGating,             {}),
]


def run_one(df_bt, klass, spread):
    engine = BacktestEngine(db_path=":memory:")
    try:
        full = engine.run(df_bt, klass, spread=spread)
    except Exception as e:
        log.warning("run failed: %s", e)
        engine.close()
        return {"pf": None, "wr": None, "trades": 0, "return": None}
    finally:
        engine.close()
    return {
        "pf": full.get("profit_factor"),
        "wr": full.get("win_rate"),
        "trades": full.get("total_trades"),
        "return": full.get("return_pct"),
    }


def main():
    data_dir = ROOT / "data"
    print(f"\n{'='*100}")
    print(f"Phase 1X-Probe Job-A+B: 戦略マトリックス (3ペア × 5戦略 × 2y)")
    print(f"{'='*100}\n")

    rows = []
    for pair, (csv_name, adx_thr) in PAIRS.items():
        csv_path = data_dir / csv_name
        if not csv_path.exists():
            print(f"⚠ {pair}: {csv_name} 未存在")
            continue
        df = load_mt5_csv(csv_path)
        df_bt = BacktestEngine.prepare_data(df)
        price = float(df_bt["Close"].iloc[-1])
        spread = calculate_spread(pair, price, pip_spread=None)

        for strat_label, strat_class, extra_kw in STRATEGIES:
            base_kw = {}
            # adx_threshold を持つ戦略は ペア別 adx_thr を反映
            if hasattr(strat_class, "adx_threshold"):
                base_kw["adx_threshold"] = adx_thr
            base_kw.update(extra_kw)
            klass = type(f"M_{pair}_{strat_label}", (strat_class,), base_kw)
            r = run_one(df_bt, klass, spread)
            rows.append({"pair": pair, "strategy": strat_label, **r})

    # 出力テーブル
    print(f"{'Pair':<10} {'Strategy':<12} | {'PF':>6} {'WR':>7} {'N':>5} {'Return':>8}")
    print("-" * 60)
    for row in rows:
        pf = f"{row['pf']:.2f}" if row['pf'] else "  -"
        wr = f"{row['wr']:.1f}%" if row['wr'] else "    -"
        ret = f"{row['return']:+.2f}%" if row['return'] else "    -"
        print(f"{row['pair']:<10} {row['strategy']:<12} | "
              f"{pf:>6} {wr:>7} {row['trades']:>5} {ret:>8}")

    # ペア別ベスト戦略
    print(f"\n{'='*60}")
    print(f"ペア別ベスト戦略 (PF最大)")
    print(f"{'='*60}")
    best = {}
    for pair in PAIRS:
        candidates = [r for r in rows
                      if r['pair'] == pair and r['pf'] is not None]
        if candidates:
            best[pair] = max(candidates, key=lambda r: r['pf'])
            r = best[pair]
            print(f"  {pair}: {r['strategy']:<12} PF={r['pf']:.2f} N={r['trades']}")

    # JSON 保存
    out = {"matrix": rows, "best_per_pair": best}
    out_json = data_dir / "phase1c_strategy_matrix.json"
    out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
