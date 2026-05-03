"""Phase 3 戦略再検証: MT5 履歴データ (M15 5年) での検証

目的:
- yfinance M15 60日 (Phase 1) と H1 730日 (Phase 2) で結論が乖離した件
- 本番タイムフレーム (M15) の長期データで定説を確立
- USD/JPY 35/65 の妥当性、EUR/USD 30/70 vs 35/65、GBP/JPY 撤退判断

データソース:
- `scripts/export_mt5_history.py` で VPS 上で生成した CSV
  例: data/mt5_USD_JPY_M15_5y.csv

戦略・グリッド:
- Phase 1/2 と完全同一の RsiPullbackADXBT
- RSI {30/70, 32/68, 35/65, 38/62} × ATR {1.5, 2.0, 2.5, 3.0, 3.5}

出力:
- data/backtest_grid_mt5_<pair>.csv
- data/phase3_mt5_summary.json
- ヒトが読むサマリは別途 docs/strategy_validation_mt5.md（手動 or 別スクリプト）
"""
from __future__ import annotations

import io
import json
import logging
import math
import sys
from pathlib import Path

# Windows コンソール (cp932) で UTF-8 出力できるよう stdout を再ラップ
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

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("phase3")
log.setLevel(logging.INFO)


# ============================================================
# 戦略 (Phase 1/2 と同一)
# ============================================================
class RsiPullbackADXBT(Strategy):
    trend_ma = 200
    rsi_period = 14
    rsi_oversold = 35
    rsi_overbought = 65
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0
    adx_period = 14
    adx_threshold = 15.0

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
# データ読込
# ============================================================
def load_mt5_csv(path: Path) -> pd.DataFrame:
    """MT5 export CSV を OHLCV DataFrame として読み込む。"""
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    expected = {"open", "high", "low", "close", "volume"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"必須カラム欠落: {missing} in {path}")
    df = df.dropna()
    return df


# ============================================================
# Sharpe SE / 95% CI
# ============================================================
def sharpe_ci(sharpe: float | None, n_trades: int) -> tuple[float, float, float] | None:
    if sharpe is None or n_trades is None or n_trades < 2:
        return None
    se = math.sqrt((1.0 + 0.5 * sharpe ** 2) / n_trades)
    return se, sharpe - 1.96 * se, sharpe + 1.96 * se


# ============================================================
# バックテスト実行
# ============================================================
def run_is_oos_wf(df_bt: pd.DataFrame, strategy_kwargs: dict, spread: float) -> dict:
    klass = type("RsiPullbackADXBT_param", (RsiPullbackADXBT,), strategy_kwargs)
    engine = BacktestEngine(db_path=":memory:")
    try:
        full = engine.run(df_bt, klass, spread=spread)
        try:
            iso = engine.run_in_out_sample(df_bt, klass, split_ratio=0.7, spread=spread)
        except Exception as e:
            log.warning("IS/OOS 失敗: %s", e)
            iso = None
        try:
            wf = engine.run_walk_forward(
                df_bt, klass, n_windows=5, auto_adjust=True, spread=spread,
            )
        except Exception as e:
            log.warning("WF 失敗: %s", e)
            wf = None
    finally:
        engine.close()

    out = {
        "full_pf": full.get("profit_factor"),
        "full_sr": full.get("sharpe_ratio"),
        "full_dd": full.get("max_drawdown"),
        "full_wr": full.get("win_rate"),
        "full_trades": full.get("total_trades"),
        "full_return": full.get("return_pct"),
    }
    if iso is not None:
        out.update({
            "is_pf": iso["in_sample"].get("profit_factor"),
            "is_sr": iso["in_sample"].get("sharpe_ratio"),
            "is_trades": iso["in_sample"].get("total_trades"),
            "oos_pf": iso["out_of_sample"].get("profit_factor"),
            "oos_sr": iso["out_of_sample"].get("sharpe_ratio"),
            "oos_trades": iso["out_of_sample"].get("total_trades"),
            "wfe_iso": iso.get("wfe"),
        })
    else:
        out.update({k: None for k in [
            "is_pf", "is_sr", "is_trades", "oos_pf", "oos_sr", "oos_trades", "wfe_iso",
        ]})
    if wf is not None:
        out["wfe_mean"] = wf.get("wfe_mean")
        out["wf_n_windows"] = len(wf.get("windows") or [])
    else:
        out["wfe_mean"] = None
        out["wf_n_windows"] = 0
    return out


# ============================================================
# メイン
# ============================================================
def main():
    pairs = {
        "USD_JPY": "mt5_USD_JPY_M15_5y.csv",
        "EUR_USD": "mt5_EUR_USD_M15_5y.csv",
        "GBP_JPY": "mt5_GBP_JPY_M15_5y.csv",
    }

    rsi_pairs = [(30, 70), (32, 68), (35, 65), (38, 62)]
    atr_mults = [1.5, 2.0, 2.5, 3.0, 3.5]

    data_dir = ROOT / "data"
    summary_per_pair: dict[str, dict] = {}

    for pair_label, csv_name in pairs.items():
        csv_path = data_dir / csv_name
        if not csv_path.exists():
            print(f"⚠ {pair_label}: {csv_name} が存在しない。スキップ。"
                  f" 先に scripts/export_mt5_history.py を VPS で実行してください。")
            continue

        print(f"\n{'='*70}\n{pair_label} — loading {csv_name}\n{'='*70}")
        df = load_mt5_csv(csv_path)
        print(f"読込: {len(df)} 本, {df.index.min()} → {df.index.max()}")

        df_bt = BacktestEngine.prepare_data(df)
        price = float(df_bt["Close"].iloc[-1])
        spread = calculate_spread(pair_label, price, pip_spread=1.0)
        print(f"代表価格 {price:.5f}, spread (相対) {spread:.8f}")

        # ----- 現状値ベースライン -----
        print(f"\n[baseline] RSI 35/65 ATR 2.0 ADX 15")
        baseline = run_is_oos_wf(df_bt, {}, spread)
        ci = sharpe_ci(baseline["full_sr"], baseline["full_trades"])
        ci_str = (
            f"[{ci[1]:+.2f}, {ci[2]:+.2f}]" if ci else "N/A"
        )
        print(
            f"  Full PF={baseline['full_pf']:.2f} SR={baseline['full_sr']:.2f} "
            f"95%CI={ci_str} Trades={baseline['full_trades']}\n"
            f"  IS PF={baseline['is_pf']} OOS PF={baseline['oos_pf']} "
            f"OOS Trades={baseline['oos_trades']}"
        )

        # ----- グリッド -----
        print(f"\n[grid] {len(rsi_pairs)} RSI × {len(atr_mults)} ATR = "
              f"{len(rsi_pairs) * len(atr_mults)} cells")
        grid_rows = []
        for rsi_lo, rsi_hi in rsi_pairs:
            for atr in atr_mults:
                kw = {
                    "rsi_oversold": rsi_lo,
                    "rsi_overbought": rsi_hi,
                    "atr_mult": atr,
                }
                r = run_is_oos_wf(df_bt, kw, spread)
                ci = sharpe_ci(r["full_sr"], r["full_trades"])
                grid_rows.append({
                    "rsi_oversold": rsi_lo,
                    "rsi_overbought": rsi_hi,
                    "atr_mult": atr,
                    "full_pf": r["full_pf"],
                    "full_sr": r["full_sr"],
                    "full_sr_ci_lo": ci[1] if ci else None,
                    "full_sr_ci_hi": ci[2] if ci else None,
                    "full_dd": r["full_dd"],
                    "full_wr": r["full_wr"],
                    "full_trades": r["full_trades"],
                    "full_return": r["full_return"],
                    "is_pf": r["is_pf"],
                    "oos_pf": r["oos_pf"],
                    "oos_trades": r["oos_trades"],
                    "wfe_iso": r["wfe_iso"],
                    "wfe_mean": r["wfe_mean"],
                })
                pf_s = f"{r['full_pf']:.2f}" if r["full_pf"] else "-"
                oos_s = f"{r['oos_pf']:.2f}" if r["oos_pf"] else "-"
                print(f"  RSI {rsi_lo}/{rsi_hi} ATR {atr}: PF={pf_s}, "
                      f"OOS PF={oos_s}, Trades={r['full_trades']}")

        out_csv = data_dir / f"backtest_grid_mt5_{pair_label}.csv"
        pd.DataFrame(grid_rows).to_csv(out_csv, index=False)
        print(f"  → {out_csv}")
        summary_per_pair[pair_label] = {
            "baseline": baseline,
            "grid": grid_rows,
            "data_path": str(csv_path.name),
            "data_bars": len(df),
        }

    out_json = data_dir / "phase3_mt5_summary.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_per_pair, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[done] summary → {out_json}")


if __name__ == "__main__":
    main()
