"""Phase 1C-1 Gate: C案 v2 着手前バックテスト検証

目的:
- C案 v2（MA200傾き + 既存 adx_threshold AND）の事前PF測定
- 過去 2026-01-01 〜 2026-04-30 の 4ヶ月で PF >= 1.5 を確認
- 通過なら Phase 1C-2 実装へ、未達なら設計やり直し or B案先行へ

C案 v2 ロジック:
1. ADX < adx_threshold → HOLD（既存と同じ）
2. |slope_pips| < MTF_TREND_MA_SLOPE_MIN_PIPS (3.0) → HOLD（C案で追加）
3. BUY: close > MA200 AND rsi < oversold AND slope_pips > 0（C案で追加 AND）
4. SELL: close < MA200 AND rsi > overbought AND slope_pips < 0（C案で追加 AND）

参考:
- _phase3_mt5_validation.py の RsiPullbackADXBT を継承
- 既存 BacktestEngine + calculate_spread を流用
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

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("phase1c_gate")
log.setLevel(logging.INFO)


# ============================================================
# Baseline 戦略（現状）
# ============================================================
class RsiPullbackADXBT(Strategy):
    """現状の MTFPullback 相当（_phase3_mt5_validation.py と同一）"""
    trend_ma = 200
    rsi_period = 14
    rsi_oversold = 35
    rsi_overbought = 65
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0
    adx_period = 14
    adx_threshold = 25.0  # pair_config の既存値（baseline）

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        self.ma_trend = self.I(ta.sma, close, length=self.trend_ma, name="MA_trend")
        self.rsi = self.I(ta.rsi, close, length=self.rsi_period, name="RSI")
        self.atr = self.I(ta.atr, high, low, close, length=self.atr_period, name="ATR")

        adx_len = self.adx_period

        def _adx_only(h, l, c):
            r = ta.adx(pd.Series(h), pd.Series(l), pd.Series(c), length=adx_len)
            if r is None:
                return pd.Series([np.nan] * len(c))
            col = f"ADX_{adx_len}"
            return r[col] if col in r.columns else pd.Series([np.nan] * len(c))

        self.adx = self.I(_adx_only, high, low, close, name="ADX")

    def next(self):
        if (
            np.isnan(self.ma_trend[-1]) or np.isnan(self.rsi[-1])
            or np.isnan(self.atr[-1]) or np.isnan(self.adx[-1])
        ):
            return
        if self.atr[-1] == 0 or self.position:
            return
        if self.adx[-1] < self.adx_threshold:
            return

        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        if price > self.ma_trend[-1] and self.rsi[-1] < self.rsi_oversold:
            self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
        elif price < self.ma_trend[-1] and self.rsi[-1] > self.rsi_overbought:
            self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)


# ============================================================
# C案 v2 戦略
# ============================================================
class RsiPullbackADXBT_CGuard(RsiPullbackADXBT):
    """C案 v2: MA200 傾き + 方向 AND を追加"""
    slope_bars = 10
    slope_min_pips = 3.0
    # pip_size は init で価格レンジから推定

    def init(self):
        super().init()
        # _JPY 判定: 価格が 10 を超えてれば JPYクロス（USDJPY ~150, EURUSD ~1.1）
        sample_price = float(pd.Series(self.data.Close).dropna().iloc[-1])
        self._pip_size = 0.01 if sample_price > 10 else 0.0001

    def next(self):
        if (
            np.isnan(self.ma_trend[-1]) or np.isnan(self.rsi[-1])
            or np.isnan(self.atr[-1]) or np.isnan(self.adx[-1])
        ):
            return
        if self.atr[-1] == 0 or self.position:
            return
        if self.adx[-1] < self.adx_threshold:
            return

        # C案ガード: slope_pips
        if len(self.ma_trend) <= self.slope_bars:
            return
        ma_now = self.ma_trend[-1]
        ma_prev = self.ma_trend[-1 - self.slope_bars]
        if np.isnan(ma_prev):
            return
        slope_pips = (ma_now - ma_prev) / self._pip_size

        if abs(slope_pips) < self.slope_min_pips:
            return  # 不確定 = HOLD

        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        if price > self.ma_trend[-1] and self.rsi[-1] < self.rsi_oversold:
            if slope_pips > 0:  # 方向AND
                self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
        elif price < self.ma_trend[-1] and self.rsi[-1] > self.rsi_overbought:
            if slope_pips < 0:  # 方向AND
                self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)


# ============================================================
# データ読込
# ============================================================
def load_mt5_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    df = df.dropna()
    return df


# ============================================================
# 単一バックテスト実行
# ============================================================
def run_one(df_bt: pd.DataFrame, klass, spread: float, label: str) -> dict:
    engine = BacktestEngine(db_path=":memory:")
    try:
        full = engine.run(df_bt, klass, spread=spread)
    finally:
        engine.close()
    return {
        "label": label,
        "pf": full.get("profit_factor"),
        "sr": full.get("sharpe_ratio"),
        "dd": full.get("max_drawdown"),
        "wr": full.get("win_rate"),
        "trades": full.get("total_trades"),
        "return": full.get("return_pct"),
    }


# ============================================================
# メイン
# ============================================================
def main():
    pairs = {
        "USD_JPY": ("mt5_USD_JPY_M15_2y.csv", 25.0),
        "EUR_USD": ("mt5_EUR_USD_M15_2y.csv", 20.0),
        "GBP_JPY": ("mt5_GBP_JPY_M15_2y.csv", 25.0),
    }

    period_start = pd.Timestamp("2026-01-01", tz="UTC")
    period_end = pd.Timestamp("2026-04-30 23:59:59", tz="UTC")

    data_dir = ROOT / "data"
    summary = {
        "gate": "Phase 1C-1",
        "criteria": "PF >= 1.5",
        "period": f"{period_start.date()} - {period_end.date()}",
        "pairs": {},
    }

    print(f"\n{'='*70}")
    print(f"Phase 1C-1 Gate Validation: C案 v2 PF >= 1.5")
    print(f"Period: {period_start.date()} → {period_end.date()}")
    print(f"{'='*70}\n")

    pf_baseline_all = []
    pf_cguard_all = []

    for pair, (csv_name, adx_thr) in pairs.items():
        csv_path = data_dir / csv_name
        if not csv_path.exists():
            print(f"⚠ {pair}: {csv_name} 未存在、スキップ")
            continue

        df = load_mt5_csv(csv_path)
        # 期間フィルタ
        df_period = df.loc[period_start:period_end]
        if len(df_period) < 500:
            print(f"⚠ {pair}: 期間内データ不足 ({len(df_period)} bars)、スキップ")
            continue

        df_bt = BacktestEngine.prepare_data(df_period)
        price = float(df_bt["Close"].iloc[-1])
        spread = calculate_spread(pair, price, pip_spread=None)

        print(f"\n{'='*70}")
        print(f"{pair}: {len(df_period)} bars, adx_threshold={adx_thr}")
        print(f"  代表価格 {price:.5f}, spread (相対) {spread:.8f}")
        print(f"{'='*70}")

        # Baseline
        klass_b = type("BaselineParam", (RsiPullbackADXBT,), {"adx_threshold": adx_thr})
        baseline = run_one(df_bt, klass_b, spread, "baseline")
        # C案
        klass_c = type("CGuardParam", (RsiPullbackADXBT_CGuard,), {"adx_threshold": adx_thr})
        cguard = run_one(df_bt, klass_c, spread, "cguard")

        # 出力
        for r in [baseline, cguard]:
            pf_s = f"{r['pf']:.2f}" if r['pf'] else "-"
            wr_s = f"{r['wr']:.1f}%" if r['wr'] else "-"
            ret_s = f"{r['return']:+.2f}%" if r['return'] else "-"
            print(
                f"  [{r['label']:>9}] PF={pf_s:>6} "
                f"WR={wr_s:>6} N={r['trades']:>4} Return={ret_s} DD={r['dd']:.1f}%"
            )

        delta_pf = (cguard['pf'] or 0) - (baseline['pf'] or 0)
        delta_n = (cguard['trades'] or 0) - (baseline['trades'] or 0)
        gate_pass = (cguard['pf'] is not None) and (cguard['pf'] >= 1.5)
        print(
            f"  → ΔPF={delta_pf:+.2f}, ΔN={delta_n:+d}, "
            f"Gate(PF>=1.5)={'PASS' if gate_pass else 'FAIL'}"
        )

        summary["pairs"][pair] = {
            "baseline": baseline,
            "cguard": cguard,
            "delta_pf": delta_pf,
            "delta_n": delta_n,
            "gate_pass": gate_pass,
        }
        if baseline['pf'] is not None:
            pf_baseline_all.append(baseline['pf'])
        if cguard['pf'] is not None:
            pf_cguard_all.append(cguard['pf'])

    # 統合判定
    summary["aggregate"] = {
        "pf_baseline_mean": (
            sum(pf_baseline_all) / len(pf_baseline_all) if pf_baseline_all else None
        ),
        "pf_cguard_mean": (
            sum(pf_cguard_all) / len(pf_cguard_all) if pf_cguard_all else None
        ),
        "all_pairs_pass": all(
            v.get("gate_pass") for v in summary["pairs"].values()
        ) if summary["pairs"] else False,
    }

    print(f"\n{'='*70}")
    print(f"統合判定")
    print(f"{'='*70}")
    print(f"  Baseline 平均PF: {summary['aggregate']['pf_baseline_mean']}")
    print(f"  C案     平均PF: {summary['aggregate']['pf_cguard_mean']}")
    print(f"  全ペアGate通過: {summary['aggregate']['all_pairs_pass']}")
    print(f"  → {'GATE PASSED — 1C-2 実装へ' if summary['aggregate']['all_pairs_pass'] else 'GATE FAILED — 設計再検討'}")

    out_json = data_dir / "phase1c_gate_summary.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
