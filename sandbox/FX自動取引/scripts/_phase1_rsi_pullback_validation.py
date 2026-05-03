"""Phase 1 戦略検証: RsiPullback バックテスト + パラメータ感度分析

目的:
- 現 RsiPullback (旧 MTFPullback) の現状値 (RSI 35/65, ATR 2.0, ADXフィルター)
  でのエッジを定量検証
- パラメータグリッド (RSI 4水準 × ATR 5水準 = 20組) で感度分析
- IS/OOS 70:30 + Walk-Forward 5窓 で WFE / 過学習診断

対象: USD_JPY, EUR_USD, GBP_JPY (M15, 60日 ~5600バー)
出力:
- data/backtest_grid_<pair>.csv
- 標準出力に集計サマリ

注意:
- yfinance の M15 は 60 日制限のため、その範囲内で検証
- 既存本番コードは変更しない (READ-ONLY)
- 戦略本体は variants_bt.MTFPullbackBT をベースに ADX フィルター追加版を新規定義
"""

from __future__ import annotations

import io
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
import yfinance as yf
from backtesting import Strategy

# プロジェクトルートを sys.path へ
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.backtester import BacktestEngine, calculate_spread  # noqa: E402

logging.basicConfig(
    level=logging.WARNING,  # バックテストの詳細ログは抑制
    format="%(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("phase1")
log.setLevel(logging.INFO)


# ============================================================
# RsiPullback + ADXフィルター の Backtesting.py アダプタ
# ============================================================
class RsiPullbackADXBT(Strategy):
    """単TF版 RsiPullback (MA200 方向 × RSI 極値) + ADX フィルター

    本番 src/strategy/rsi_pullback.py + ADXフィルター(F15) と同等ロジック。
    クラス属性で optimize() / 手動グリッドに対応。
    """

    trend_ma = 200
    rsi_period = 14
    rsi_oversold = 35
    rsi_overbought = 65
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0
    adx_period = 14
    adx_threshold = 15.0  # config.ADX_THRESHOLD と同じ既定

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        self.ma_trend = self.I(
            ta.sma, close, length=self.trend_ma, name="MA_trend"
        )
        self.rsi = self.I(
            ta.rsi, close, length=self.rsi_period, name="RSI"
        )
        self.atr = self.I(
            ta.atr, high, low, close, length=self.atr_period, name="ATR"
        )

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
            np.isnan(self.ma_trend[-1])
            or np.isnan(self.rsi[-1])
            or np.isnan(self.atr[-1])
            or np.isnan(self.adx[-1])
        ):
            return
        if self.atr[-1] == 0 or self.position:
            return
        # ADX フィルター: 弱トレンドはスキップ
        if self.adx[-1] < self.adx_threshold:
            return

        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        # 上昇トレンド + RSI 過売 → 押し目買い
        if price > self.ma_trend[-1] and self.rsi[-1] < self.rsi_oversold:
            self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
        # 下降トレンド + RSI 過熱 → 戻り売り
        elif price < self.ma_trend[-1] and self.rsi[-1] > self.rsi_overbought:
            self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)


# ============================================================
# データ取得
# ============================================================
def fetch_yf(symbol: str, period: str = "60d", interval: str = "15m") -> pd.DataFrame:
    """yfinance から OHLCV を取得し、小文字カラムの DataFrame で返す。"""
    raw = yf.download(
        symbol, period=period, interval=interval,
        progress=False, auto_adjust=False,
    )
    if raw.empty:
        raise RuntimeError(f"yfinance: 空データ ({symbol})")

    # MultiIndex カラム → 単純化
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [c[0] for c in raw.columns]

    df = pd.DataFrame({
        "open": raw["Open"].astype(float),
        "high": raw["High"].astype(float),
        "low": raw["Low"].astype(float),
        "close": raw["Close"].astype(float),
        "volume": raw["Volume"].astype(float),
    })
    df.index = raw.index
    df = df.dropna()
    return df


# ============================================================
# Sharpe SE / 95% CI ヘルパー
# ============================================================
def sharpe_ci(sharpe: float | None, n_trades: int) -> tuple[float, float, float] | None:
    """Sharpe Ratio の標準誤差と 95% CI を近似計算。

    Lo (2002) の単純近似: SE ≈ sqrt((1 + 0.5 * SR^2) / N)
    """
    if sharpe is None or n_trades is None or n_trades < 2:
        return None
    se = math.sqrt((1.0 + 0.5 * sharpe ** 2) / n_trades)
    return se, sharpe - 1.96 * se, sharpe + 1.96 * se


# ============================================================
# 単発バックテスト + IS/OOS + WF
# ============================================================
def run_single_backtest(
    df_bt: pd.DataFrame,
    strategy_kwargs: dict,
    spread: float,
) -> dict:
    """単一区間のバックテストを実行。"""
    # 動的にサブクラスを作る (各 grid 用にパラメータを反映)
    klass = type(
        "RsiPullbackADXBT_param",
        (RsiPullbackADXBT,),
        strategy_kwargs,
    )
    engine = BacktestEngine(db_path=":memory:")
    try:
        return engine.run(df_bt, klass, spread=spread)
    finally:
        engine.close()


def run_is_oos_wf(
    df_bt: pd.DataFrame,
    strategy_kwargs: dict,
    spread: float,
) -> dict:
    """IS/OOS 70:30 + WF 5窓 をまとめて実行し、平坦な dict を返す。"""
    klass = type(
        "RsiPullbackADXBT_param",
        (RsiPullbackADXBT,),
        strategy_kwargs,
    )
    engine = BacktestEngine(db_path=":memory:")
    try:
        # 全期間
        full = engine.run(df_bt, klass, spread=spread)
        # IS/OOS
        try:
            iso = engine.run_in_out_sample(
                df_bt, klass, split_ratio=0.7, spread=spread,
            )
        except Exception as e:
            log.warning("IS/OOS 失敗: %s", e)
            iso = None
        # Walk-Forward
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
            "is_pf", "is_sr", "is_trades",
            "oos_pf", "oos_sr", "oos_trades", "wfe_iso",
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
        "USD_JPY": ("USDJPY=X", "USD_JPY"),
        "EUR_USD": ("EURUSD=X", "EUR_USD"),
        "GBP_JPY": ("GBPJPY=X", "GBP_JPY"),
    }

    # グリッド: RSI 4 × ATR 5 = 20 組
    rsi_pairs = [(30, 70), (32, 68), (35, 65), (38, 62)]
    atr_mults = [1.5, 2.0, 2.5, 3.0, 3.5]

    out_dir = ROOT / "data"
    out_dir.mkdir(exist_ok=True)

    summary_per_pair: dict[str, dict] = {}

    for pair_label, (yf_sym, instrument) in pairs.items():
        print(f"\n{'='*70}\n{pair_label} ({yf_sym}) — fetching M15 60日\n{'='*70}")
        try:
            df = fetch_yf(yf_sym, period="60d", interval="15m")
        except Exception as e:
            log.error("%s データ取得失敗: %s", pair_label, e)
            continue
        print(f"取得: {len(df)} 本, {df.index.min()} → {df.index.max()}")

        df_bt = BacktestEngine.prepare_data(df)
        price = float(df_bt["Close"].iloc[-1])
        spread = calculate_spread(instrument, price, pip_spread=1.0)
        print(f"代表価格 {price:.5f}, spread (相対) {spread:.8f}")

        # ----- 1. 現状値で IS/OOS + WF -----
        print(f"\n[1] 現状値 (RSI 35/65, ATR 2.0, ADX 15) IS/OOS + WF")
        baseline_kwargs = dict(
            rsi_oversold=35, rsi_overbought=65,
            atr_mult=2.0, adx_threshold=15.0,
        )
        baseline = run_is_oos_wf(df_bt, baseline_kwargs, spread)

        # SE/CI (full 区間)
        ci = sharpe_ci(baseline["full_sr"], baseline["full_trades"])
        if ci is not None:
            se, lo, hi = ci
            baseline["full_sr_se"] = se
            baseline["full_sr_ci_low"] = lo
            baseline["full_sr_ci_high"] = hi
        else:
            baseline.update({
                "full_sr_se": None,
                "full_sr_ci_low": None,
                "full_sr_ci_high": None,
            })

        for k, v in baseline.items():
            if isinstance(v, float):
                print(f"  {k:18s} = {v:.4f}")
            else:
                print(f"  {k:18s} = {v}")

        # ----- 2. グリッド感度分析 (full + IS/OOS + WF) -----
        print(f"\n[2] グリッド感度分析 (RSI 4 × ATR 5 = 20 組)")
        rows = []
        for rsi_lo, rsi_hi in rsi_pairs:
            for atr_m in atr_mults:
                kw = dict(
                    rsi_oversold=rsi_lo,
                    rsi_overbought=rsi_hi,
                    atr_mult=atr_m,
                    adx_threshold=15.0,
                )
                try:
                    res = run_is_oos_wf(df_bt, kw, spread)
                except Exception as e:
                    log.warning("グリッド失敗 RSI=%d/%d ATR=%.1f: %s",
                                rsi_lo, rsi_hi, atr_m, e)
                    continue
                row = {
                    "pair": pair_label,
                    "rsi_oversold": rsi_lo,
                    "rsi_overbought": rsi_hi,
                    "atr_mult": atr_m,
                    **res,
                }
                rows.append(row)
                pf = res.get("full_pf")
                sr = res.get("full_sr")
                t = res.get("full_trades")
                wfe_iso = res.get("wfe_iso")
                wfe_m = res.get("wfe_mean")
                print(
                    f"  RSI {rsi_lo:>2}/{rsi_hi:<2} ATR {atr_m:.1f} → "
                    f"PF={pf or 0:.2f} SR={sr or 0:.2f} "
                    f"Trades={t or 0:>3} "
                    f"WFE_iso={wfe_iso if wfe_iso is None else round(wfe_iso, 2)} "
                    f"WFE_mean={wfe_m if wfe_m is None else round(wfe_m, 2)}"
                )

        # CSV 保存
        df_grid = pd.DataFrame(rows)
        csv_path = out_dir / f"backtest_grid_{pair_label}.csv"
        df_grid.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"\nCSV 保存: {csv_path}")

        # ----- 3. 過学習診断 -----
        if not df_grid.empty:
            # IS PF 最高 vs OOS PF 最高 のパラメータ一致?
            is_max = df_grid.loc[df_grid["is_pf"].idxmax()] if df_grid["is_pf"].notna().any() else None
            oos_max = df_grid.loc[df_grid["oos_pf"].idxmax()] if df_grid["oos_pf"].notna().any() else None

            wfe_robust = df_grid[
                df_grid["wfe_mean"].notna() & (df_grid["wfe_mean"] >= 0.5)
            ]

            def _fmt(v):
                return "NA" if v is None or (isinstance(v, float) and pd.isna(v)) else f"{v:.2f}"

            print(f"\n[3] 過学習診断")
            if is_max is not None:
                print(
                    f"  IS PF max:  RSI {int(is_max['rsi_oversold'])}/{int(is_max['rsi_overbought'])} "
                    f"ATR {is_max['atr_mult']:.1f} → "
                    f"IS PF={_fmt(is_max['is_pf'])}, OOS PF={_fmt(is_max['oos_pf'])}"
                )
            if oos_max is not None:
                print(
                    f"  OOS PF max: RSI {int(oos_max['rsi_oversold'])}/{int(oos_max['rsi_overbought'])} "
                    f"ATR {oos_max['atr_mult']:.1f} → "
                    f"OOS PF={_fmt(oos_max['oos_pf'])}, IS PF={_fmt(oos_max['is_pf'])}"
                )
            same_param = (
                is_max is not None and oos_max is not None
                and int(is_max["rsi_oversold"]) == int(oos_max["rsi_oversold"])
                and float(is_max["atr_mult"]) == float(oos_max["atr_mult"])
            )
            print(f"  IS最適 == OOS最適: {same_param}")
            print(f"  WFE_mean >= 0.5 のロバストパラメータ: {len(wfe_robust)} 件 / {len(df_grid)} 件")
            if not wfe_robust.empty:
                for _, r in wfe_robust.sort_values("wfe_mean", ascending=False).head(5).iterrows():
                    print(
                        f"    RSI {int(r['rsi_oversold'])}/{int(r['rsi_overbought'])} "
                        f"ATR {r['atr_mult']:.1f}: WFE_mean={r['wfe_mean']:.2f}, "
                        f"OOS PF={_fmt(r['oos_pf'])}, OOS Trades={r['oos_trades']}"
                    )

        summary_per_pair[pair_label] = {
            "n_bars": int(len(df_bt)),
            "baseline": baseline,
            "grid_rows": rows,
        }

    # ----- 全体サマリ JSON -----
    import json
    sum_path = out_dir / "phase1_validation_summary.json"
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary_per_pair, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nサマリ JSON: {sum_path}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
