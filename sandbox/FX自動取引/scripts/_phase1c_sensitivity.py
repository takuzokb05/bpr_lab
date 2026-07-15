"""Phase 1X-Sensitivity: 過去データ感度分析

karen 反論への定量回答:
- 期間感度（4ヶ月切りの恣意性検証）: 1mo / 3mo / 6mo / 1y / 2y
- ペア感度（USD_JPY との一貫性）: USD_JPY / EUR_USD / GBP_JPY
- 戦略感度（Baseline vs C案 v2）
- 本番再現性（本番期間 2026-04-21〜05-04 同期間BT vs 本番実績）

入力: data/mt5_*_M15_2y.csv（2年分のM15）
出力: data/phase1c_sensitivity.json + 標準出力テーブル
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

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.backtester import BacktestEngine, calculate_spread  # noqa: E402

# Gate スクリプトから戦略クラスを再利用（dual definitionを避ける）
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location(
    "_phase1c_gate", Path(__file__).parent / "_phase1c_gate_validation.py",
)
gate_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate_mod)
RsiPullbackADXBT = gate_mod.RsiPullbackADXBT
RsiPullbackADXBT_CGuard = gate_mod.RsiPullbackADXBT_CGuard
load_mt5_csv = gate_mod.load_mt5_csv

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("phase1c_sens")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
PERIODS = [
    ("1mo", "2026-04-01", "2026-04-30"),
    ("3mo", "2026-02-01", "2026-04-30"),
    ("6mo", "2025-11-01", "2026-04-30"),
    ("1y",  "2025-05-01", "2026-04-30"),
    ("2y",  "2024-05-01", "2026-04-30"),
]

PAIRS = {
    # pair: (csv name, pair_config adx_threshold)
    "USD_JPY": ("mt5_USD_JPY_M15_2y.csv", 20.0),
    "EUR_USD": ("mt5_EUR_USD_M15_2y.csv", 25.0),
    "GBP_JPY": ("mt5_GBP_JPY_M15_2y.csv", 25.0),
}

STRATEGIES = [
    ("baseline", RsiPullbackADXBT),
    ("cguard",   RsiPullbackADXBT_CGuard),
]

# 本番実績（DB 集計済み、固定値）
PROD_RECORD = {
    "USD_JPY": {"n": 8,  "wins": 1,  "pl": -6817.0},
    "EUR_USD": {"n": 14, "wins": 5,  "pl": +3029.0},
    "GBP_JPY": {"n": 38, "wins": 13, "pl": -2004.0},
}
# 本番期間（trades テーブルの opened_at min/max）
PROD_PERIOD = ("2026-04-21", "2026-05-04")


# ============================================================
# 単一バックテスト
# ============================================================
def run_one(df_bt: pd.DataFrame, klass, spread: float) -> dict:
    engine = BacktestEngine(db_path=":memory:")
    try:
        full = engine.run(df_bt, klass, spread=spread)
    except Exception as e:
        log.warning("run failed: %s", e)
        engine.close()
        return {"pf": None, "wr": None, "trades": None, "return": None, "dd": None}
    finally:
        engine.close()
    return {
        "pf": full.get("profit_factor"),
        "wr": full.get("win_rate"),
        "trades": full.get("total_trades"),
        "return": full.get("return_pct"),
        "dd": full.get("max_drawdown"),
    }


def fmt_cell(r: dict) -> str:
    pf = f"{r['pf']:.2f}" if r['pf'] else "  - "
    n = r['trades'] or 0
    return f"{pf}/{n:>3}"


# ============================================================
# メイン
# ============================================================
def main():
    data_dir = ROOT / "data"
    rows = []

    print(f"\n{'='*100}")
    print(f"Phase 1X-Sensitivity: 過去データ感度分析")
    print(f"観点1+5: 期間×ペア×戦略 (PF/N グリッド)")
    print(f"{'='*100}")

    # 観点1+2+5: 期間 × ペア × 戦略 グリッド
    grid_table = {}  # {pair: {strategy: {period: {pf, n, wr, return}}}}
    for pair, (csv_name, adx_thr) in PAIRS.items():
        csv_path = data_dir / csv_name
        if not csv_path.exists():
            print(f"⚠ {pair}: {csv_name} 未存在、スキップ")
            continue
        df_full = load_mt5_csv(csv_path)
        grid_table[pair] = {}

        for strat_label, strat_class in STRATEGIES:
            grid_table[pair][strat_label] = {}

            for period_label, start_str, end_str in PERIODS:
                # tz aware
                start = pd.Timestamp(start_str, tz="UTC")
                end = pd.Timestamp(end_str + " 23:59:59", tz="UTC")
                df_period = df_full.loc[start:end]
                if len(df_period) < 500:
                    grid_table[pair][strat_label][period_label] = {
                        "pf": None, "trades": 0, "skipped": True,
                    }
                    continue

                df_bt = BacktestEngine.prepare_data(df_period)
                price = float(df_bt["Close"].iloc[-1])
                spread = calculate_spread(pair, price, pip_spread=None)

                klass = type(f"P_{pair}_{strat_label}_{period_label}",
                             (strat_class,), {"adx_threshold": adx_thr})
                r = run_one(df_bt, klass, spread)
                grid_table[pair][strat_label][period_label] = r
                rows.append({
                    "pair": pair, "strategy": strat_label, "period": period_label,
                    **r,
                })

    # 表出力
    print()
    print(f"{'Pair':<10} {'Strategy':<10} | " + " | ".join(f"{p[0]:>9}" for p in PERIODS))
    print("-" * 90)
    for pair in PAIRS:
        if pair not in grid_table:
            continue
        for strat_label, _ in STRATEGIES:
            cells = []
            for period_label, _, _ in PERIODS:
                r = grid_table[pair][strat_label].get(period_label, {})
                if r.get("skipped"):
                    cells.append("    -    ")
                else:
                    cells.append(f"{fmt_cell(r):>9}")
            print(f"{pair:<10} {strat_label:<10} | " + " | ".join(cells))

    # 観点3: 本番再現性
    print(f"\n{'='*100}")
    print(f"観点3: 本番再現性 (期間 {PROD_PERIOD[0]}〜{PROD_PERIOD[1]})")
    print(f"{'='*100}")
    prod_repro = {}
    start = pd.Timestamp(PROD_PERIOD[0], tz="UTC")
    end = pd.Timestamp(PROD_PERIOD[1] + " 23:59:59", tz="UTC")
    print(f"{'Pair':<10} {'本番N':>6} {'本番勝率':>9} {'本番PL':>9} | "
          f"{'BT N':>5} {'BT PF':>7} {'BT WR':>7} {'BT Ret':>8}")
    print("-" * 80)
    for pair, (csv_name, adx_thr) in PAIRS.items():
        csv_path = data_dir / csv_name
        if not csv_path.exists():
            continue
        df_full = load_mt5_csv(csv_path)
        df_period = df_full.loc[start:end]
        if len(df_period) < 100:
            print(f"{pair:<10} データ不足")
            continue
        df_bt = BacktestEngine.prepare_data(df_period)
        spread = calculate_spread(pair, float(df_bt["Close"].iloc[-1]), pip_spread=None)
        klass = type(f"PR_{pair}", (RsiPullbackADXBT,), {"adx_threshold": adx_thr})
        bt_r = run_one(df_bt, klass, spread)
        prod_r = PROD_RECORD[pair]
        prod_wr = (prod_r["wins"] / prod_r["n"]) * 100
        prod_repro[pair] = {"prod": prod_r, "bt": bt_r}
        bt_pf_s = f"{bt_r['pf']:.2f}" if bt_r['pf'] else "-"
        bt_wr_s = f"{bt_r['wr']:.1f}%" if bt_r['wr'] else "-"
        bt_ret_s = f"{bt_r['return']:+.2f}%" if bt_r['return'] else "-"
        print(f"{pair:<10} {prod_r['n']:>6} {prod_wr:>8.1f}% {prod_r['pl']:>+9.0f} | "
              f"{bt_r['trades']:>5} {bt_pf_s:>7} {bt_wr_s:>7} {bt_ret_s:>8}")

    # 観点4: PF の期間内安定性（簡易版、Bootstrap の代替）
    print(f"\n{'='*100}")
    print(f"観点4: PF期間内安定性 (各ペア×戦略、期間別PFのレンジと中央値)")
    print(f"{'='*100}")
    print(f"{'Pair':<10} {'Strategy':<10} | {'PF最小':>7} {'PF中央':>7} {'PF最大':>7} | {'解釈':<30}")
    print("-" * 80)
    for pair in PAIRS:
        if pair not in grid_table:
            continue
        for strat_label, _ in STRATEGIES:
            pfs = [r['pf'] for r in grid_table[pair][strat_label].values()
                   if r.get('pf') is not None]
            if not pfs:
                continue
            pfs_sorted = sorted(pfs)
            pf_min = pfs_sorted[0]
            pf_max = pfs_sorted[-1]
            pf_med = pfs_sorted[len(pfs_sorted) // 2]
            # 解釈
            if pf_max < 1.0:
                interp = "全期間で負け（撤退筋）"
            elif pf_min > 1.5:
                interp = "全期間で安定勝ち"
            elif pf_min > 1.0:
                interp = "全期間で利益"
            else:
                interp = "期間依存（不安定）"
            print(f"{pair:<10} {strat_label:<10} | "
                  f"{pf_min:>7.2f} {pf_med:>7.2f} {pf_max:>7.2f} | {interp:<30}")

    # JSON 保存
    out = {
        "grid": grid_table,
        "prod_reproducibility": prod_repro,
        "periods": PERIODS,
        "pairs": list(PAIRS.keys()),
        "strategies": [s[0] for s in STRATEGIES],
    }
    out_json = data_dir / "phase1c_sensitivity.json"
    out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
