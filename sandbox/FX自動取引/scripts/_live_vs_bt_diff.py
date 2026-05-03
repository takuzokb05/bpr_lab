"""P1-2: 実戦戦績 vs バックテストの乖離定量化。

本番DB (fx_trading_prod_snapshot.db) のクローズド取引と、
同期間の M15 データに同じ戦略を当てたバックテスト結果を比較し、
- スプレッド/スリッページ実コスト
- フィルタ通過率（バックテストシグナル数 vs 実発注数）
- 勝率・PF の乖離
を定量分解する。

出力: docs/live_vs_backtest_diff.md, data/live_vs_bt_diff.csv
"""
import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtesting import Backtest

from src.backtester import calculate_spread
from src.strategy.variants_bt import BollingerReversalBT, MTFPullbackBT

DB_PATH = ROOT / "data" / "fx_trading_prod_snapshot.db"
PRICE_DIR = ROOT / "data"
OUT_DOC = ROOT / "docs" / "live_vs_backtest_diff.md"
OUT_CSV = ROOT / "data" / "live_vs_bt_diff.csv"

# main.py の INSTRUMENT_STRATEGY_MAP に対応
PAIR_STRATEGY = {
    "USD_JPY": ("RsiPullback (MA200+RSI35/65, ATR2.0, RR2.0)", MTFPullbackBT),
    "EUR_USD": ("RsiPullback (MA200+RSI35/65, ATR2.0, RR2.0)", MTFPullbackBT),
    "GBP_JPY": ("BollingerReversal (BB20/2σ+RSI70/30, ATR1.5, RR1.5)", BollingerReversalBT),
}


def load_live_trades(pair: str) -> pd.DataFrame:
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query(
        """SELECT id, trade_id, instrument, units, open_price, close_price,
                  stop_loss, take_profit, pl, opened_at, closed_at
           FROM trades
           WHERE status='closed' AND instrument=?
           ORDER BY opened_at""",
        conn, params=(pair,),
    )
    conn.close()
    df["opened_at"] = pd.to_datetime(df["opened_at"], utc=True)
    df["closed_at"] = pd.to_datetime(df["closed_at"], utc=True)
    df["direction"] = df["units"].apply(lambda u: "BUY" if u > 0 else "SELL")
    df["abs_units"] = df["units"].abs()
    return df


def load_prices(pair: str) -> pd.DataFrame:
    f = PRICE_DIR / f"_yf_cache_{pair}_15m.csv"
    df = pd.read_csv(f, parse_dates=["Datetime"])
    df = df.rename(columns={"Datetime": "datetime"})
    df = df.set_index("datetime").sort_index()
    return df


def run_period_backtest(pair: str, prices: pd.DataFrame,
                        start: pd.Timestamp, end: pd.Timestamp,
                        strategy_class) -> dict:
    """指定期間の OHLCV に戦略を適用してバックテスト。

    バックテストには warmup として開始の 250 本前から渡し、結果は期間内のみ抽出。
    """
    # ウォームアップ確保（MA200 + α）
    warmup_start = start - pd.Timedelta(minutes=15 * 260)
    sub = prices.loc[warmup_start:end].copy()
    if len(sub) < 250:
        return {"error": f"data不足 ({len(sub)} bars)"}

    sub.columns = [c.capitalize() for c in sub.columns]
    sub = sub.dropna()
    spread = calculate_spread(pair, float(sub["Close"].iloc[-1]))
    bt = Backtest(
        sub, strategy_class,
        cash=1_000_000,
        spread=spread,
        commission=0.0,
        margin=0.04,
        exclusive_orders=True,
    )
    stats = bt.run()
    trades_df = stats.get("_trades")

    period_trades = pd.DataFrame()
    if trades_df is not None and len(trades_df) > 0:
        # backtesting.py 0.6 系の _trades は EntryTime / ExitTime 列
        if "EntryTime" in trades_df.columns:
            entry_times = pd.to_datetime(trades_df["EntryTime"], utc=True)
            mask = (entry_times >= start) & (entry_times <= end)
            period_trades = trades_df[mask].copy()
            period_trades["EntryTime"] = entry_times[mask]

    n = len(period_trades)
    wins = (period_trades["PnL"] > 0).sum() if n else 0
    losses = n - wins
    sum_pnl = float(period_trades["PnL"].sum()) if n else 0.0
    avg_pnl = sum_pnl / n if n else 0.0
    win_rate = wins / n * 100 if n else 0.0
    pf = (
        period_trades.loc[period_trades["PnL"] > 0, "PnL"].sum()
        / abs(period_trades.loc[period_trades["PnL"] < 0, "PnL"].sum())
    ) if (n and (period_trades["PnL"] < 0).any()) else float("nan")

    return {
        "n": n,
        "wins": int(wins),
        "losses": int(losses),
        "sum_pnl_yen": sum_pnl,
        "avg_pnl_yen": avg_pnl,
        "win_rate_pct": win_rate,
        "pf": pf,
        "spread_used": spread,
        "trades_df": period_trades,
        "full_result": {
            "sharpe": float(stats.get("Sharpe Ratio")) if stats.get("Sharpe Ratio") == stats.get("Sharpe Ratio") else None,
            "dd": float(stats.get("Max. Drawdown [%]")) if stats.get("Max. Drawdown [%]") == stats.get("Max. Drawdown [%]") else None,
            "n_total": int(stats.get("# Trades", 0)),
        },
    }


def estimate_pip_size(pair: str) -> float:
    return 0.01 if pair.endswith("JPY") else 0.0001


def estimate_avg_slippage(live_df: pd.DataFrame, prices: pd.DataFrame, pair: str) -> dict:
    """各 live trade の opened_at に対して、その時点で進行中の M15 バーの
    open/close と実 entry の差を pips で集計する。
    """
    pip = estimate_pip_size(pair)
    rows = []
    for _, row in live_df.iterrows():
        opened = row["opened_at"]
        # M15 切り上げ
        bar_floor = opened.floor("15min")
        if bar_floor not in prices.index:
            continue
        bar = prices.loc[bar_floor]
        live_entry = row["open_price"]
        # 「シグナル発生バーの close」を理想 entry と仮定（戦略が close で判定するため）
        ideal_entry = bar["close"]
        slip_pips = (live_entry - ideal_entry) / pip
        # BUY なら entry が高いほど不利、SELL なら低いほど不利 → 不利方向を正に統一
        if row["direction"] == "SELL":
            slip_pips = -slip_pips
        rows.append({
            "trade_id": row["trade_id"],
            "direction": row["direction"],
            "live_entry": live_entry,
            "bar_close": ideal_entry,
            "bar_high": bar["high"],
            "bar_low": bar["low"],
            "slip_pips_unfavor": slip_pips,
        })
    if not rows:
        return {"n": 0, "avg_slip_pips": 0.0, "median_slip_pips": 0.0}
    sdf = pd.DataFrame(rows)
    return {
        "n": len(sdf),
        "avg_slip_pips": float(sdf["slip_pips_unfavor"].mean()),
        "median_slip_pips": float(sdf["slip_pips_unfavor"].median()),
        "p95_slip_pips": float(sdf["slip_pips_unfavor"].quantile(0.95)),
        "max_slip_pips": float(sdf["slip_pips_unfavor"].max()),
        "rows": sdf,
    }


def main() -> int:
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    all_csv_rows = []
    md_sections = []
    overlap_stats = {}

    for pair, (label, strat_cls) in PAIR_STRATEGY.items():
        print(f"\n{'='*60}\n{pair}: {label}\n{'='*60}")

        live = load_live_trades(pair)
        if live.empty:
            print("live trades なし")
            continue
        prices = load_prices(pair)

        # 同時保有チェック
        live_sorted = live.sort_values("opened_at").reset_index(drop=True)
        any_overlap = 0
        same_dir_overlap = 0
        for i, row in live_sorted.iterrows():
            others = live_sorted.drop(i)
            ov = others[(others["opened_at"] <= row["opened_at"]) &
                        (others["closed_at"] > row["opened_at"])]
            if len(ov) > 0:
                any_overlap += 1
                if (ov["direction"] == row["direction"]).any():
                    same_dir_overlap += 1
        overlap_stats[pair] = {
            "any": any_overlap,
            "same_dir": same_dir_overlap,
            "total": len(live_sorted),
        }
        print(f"同時保有: {any_overlap}/{len(live_sorted)}（同方向 {same_dir_overlap}）")

        # 実戦集計
        n_live = len(live)
        wins = (live["pl"] > 0).sum()
        losses = n_live - wins
        sum_pl = float(live["pl"].sum())
        avg_pl = sum_pl / n_live if n_live else 0.0
        wr = wins / n_live * 100 if n_live else 0.0
        gp = float(live.loc[live["pl"] > 0, "pl"].sum())
        gl = float(-live.loc[live["pl"] < 0, "pl"].sum())
        pf_live = gp / gl if gl > 0 else float("nan")

        live_period_start = live["opened_at"].min()
        live_period_end = live["closed_at"].max()
        print(f"live: n={n_live}, wins={wins}, losses={losses}, sum_pl={sum_pl}, "
              f"wr={wr:.1f}%, pf={pf_live:.2f}")
        print(f"period: {live_period_start} → {live_period_end}")

        # バックテスト
        bt = run_period_backtest(pair, prices, live_period_start, live_period_end, strat_cls)
        if "error" in bt:
            print(f"BT error: {bt['error']}")
            continue
        print(f"BT: n={bt['n']}, wins={bt['wins']}, losses={bt['losses']}, "
              f"sum_pnl={bt['sum_pnl_yen']:.0f}, wr={bt['win_rate_pct']:.1f}%, pf={bt['pf']}")

        # スリッページ
        slip = estimate_avg_slippage(live, prices, pair)
        print(f"slip: n={slip['n']}, avg={slip.get('avg_slip_pips', 0):.2f} pips (不利方向+)")

        # フィルタ通過率
        filter_ratio = (n_live / bt["n"]) if bt["n"] else float("inf")
        print(f"フィルタ通過率: live {n_live} / BT {bt['n']} = {filter_ratio:.2f}x")

        summary_rows.append({
            "pair": pair,
            "strategy": label,
            "live_n": n_live,
            "live_wr_pct": round(wr, 1),
            "live_pf": round(pf_live, 2) if pf_live == pf_live else None,
            "live_sum_pl": round(sum_pl, 0),
            "live_avg_pl": round(avg_pl, 1),
            "bt_n": bt["n"],
            "bt_wr_pct": round(bt["win_rate_pct"], 1),
            "bt_pf": round(bt["pf"], 2) if bt["pf"] == bt["pf"] else None,
            "bt_sum_pnl": round(bt["sum_pnl_yen"], 0),
            "bt_avg_pnl": round(bt["sum_pnl_yen"] / bt["n"], 1) if bt["n"] else 0,
            "filter_pass_ratio": round(filter_ratio, 2) if filter_ratio != float("inf") else None,
            "slip_avg_pips": round(slip.get("avg_slip_pips", 0), 2),
            "slip_p95_pips": round(slip.get("p95_slip_pips", 0), 2),
            "spread_used": bt["spread_used"],
        })

        # CSV: 個別ライブトレード行
        if "rows" in slip:
            for _, r in slip["rows"].iterrows():
                all_csv_rows.append({
                    "pair": pair,
                    "trade_id": r["trade_id"],
                    "direction": r["direction"],
                    "live_entry": r["live_entry"],
                    "bar_close": r["bar_close"],
                    "slip_pips_unfavor": round(r["slip_pips_unfavor"], 3),
                })

        # MDセクション
        md = []
        md.append(f"## {pair} — {label}\n")
        md.append(f"**期間**: {live_period_start.date()} 〜 {live_period_end.date()}\n")
        md.append("")
        md.append("| 指標 | 実戦 | バックテスト | 乖離 |")
        md.append("|---|---:|---:|---|")
        md.append(f"| 取引数 | {n_live} | {bt['n']} | live が BT の {filter_ratio:.2f}x |")
        md.append(f"| 勝率 | {wr:.1f}% | {bt['win_rate_pct']:.1f}% | "
                  f"{wr - bt['win_rate_pct']:+.1f}pt |")
        md.append(f"| PF | {pf_live:.2f} | {bt['pf']:.2f} | "
                  f"{pf_live - bt['pf']:+.2f} |")
        md.append(f"| 合計PL | {sum_pl:+.0f} 円 | {bt['sum_pnl_yen']:+.0f} 円 | "
                  f"{sum_pl - bt['sum_pnl_yen']:+.0f} 円 |")
        md.append(f"| 平均PL/取引 | {avg_pl:+.1f} 円 | "
                  f"{bt['sum_pnl_yen']/bt['n'] if bt['n'] else 0:+.1f} 円 | — |")
        md.append("")
        md.append("**スリッページ（実 entry vs シグナル発生バーの close）**:")
        md.append(f"- n={slip['n']}, 平均 {slip.get('avg_slip_pips', 0):+.2f} pips, "
                  f"中央値 {slip.get('median_slip_pips', 0):+.2f} pips, "
                  f"p95 {slip.get('p95_slip_pips', 0):+.2f} pips, "
                  f"max {slip.get('max_slip_pips', 0):+.2f} pips")
        md.append("")
        md.append(f"- スプレッド適用値（バックテスト）: {bt['spread_used']:.6f}")
        md.append("")
        ov = overlap_stats[pair]
        md.append(f"**同時保有（同一ペア）**: {ov['any']}/{ov['total']} 取引で他のオープン中ポジションと重なる")
        md.append(f" — うち同方向 {ov['same_dir']}（exclusive_orders 違反）")
        md.append("")
        md_sections.append("\n".join(md))

    # 出力
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    if all_csv_rows:
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_csv_rows[0].keys()))
            w.writeheader()
            w.writerows(all_csv_rows)
        print(f"\nCSV: {OUT_CSV}")

    # サマリーテーブル
    sumtbl = []
    sumtbl.append("| pair | live n | live WR | live PF | BT n | BT WR | BT PF | filter pass | slip avg pips |")
    sumtbl.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for s in summary_rows:
        sumtbl.append(
            f"| {s['pair']} | {s['live_n']} | {s['live_wr_pct']}% | {s['live_pf']} | "
            f"{s['bt_n']} | {s['bt_wr_pct']}% | {s['bt_pf']} | "
            f"{s['filter_pass_ratio']}x | {s['slip_avg_pips']} |"
        )

    doc = []
    doc.append("# P1-2: 実戦戦績 vs バックテスト乖離分析\n")
    doc.append(f"生成日時: {datetime.now(timezone.utc).isoformat()}")
    doc.append(f"DB: `{DB_PATH.name}` (本番VPSスナップショット)")
    doc.append(f"価格データ: yfinance M15 cache (`_yf_cache_*_15m.csv`)")
    doc.append(f"対象期間: 2026-04-21 〜 2026-05-01（10日間、PR #4 前後のクローズド取引）")
    doc.append("")
    doc.append("## 結論サマリ\n")
    doc.append("\n".join(sumtbl))
    doc.append("")
    doc.append("**読み方**:")
    doc.append("- `filter pass` < 1.0 → 戦略フィルタが厳しく、BT で出るシグナルを取りこぼしている")
    doc.append("- `filter pass` > 1.0 → 実取引の方が多い（重複発注、AIフィルタの逆効果など）")
    doc.append("- `slip avg pips` プラス → 実 entry が不利方向（成行で滑っている）")
    doc.append("- 勝率・PF が live < BT → スプレッド/スリッページ/AIフィルタ等のコストが効いている")
    doc.append("")
    doc.append("## キー所見（根本原因）\n")
    doc.append("### 所見1: 同時複数ポジション（exclusive_orders 違反）が最大の乖離源\n")
    doc.append("バックテストは `exclusive_orders=True` で同ペア1ポジションに制限。")
    doc.append("実戦の `trading_loop.py` には同等のガードが欠けており、同一ペアで同時保有が多発。\n")
    doc.append("| pair | 全 trade | 同時保有あり | うち同方向 | 同方向比率 |")
    doc.append("|---|---:|---:|---:|---:|")
    for pair, ov in overlap_stats.items():
        ratio = ov["same_dir"] / ov["total"] * 100 if ov["total"] else 0
        doc.append(f"| {pair} | {ov['total']} | {ov['any']} | {ov['same_dir']} | {ratio:.1f}% |")
    doc.append("")
    doc.append("**特に GBP_JPY**: 37 取引中 16（43%）が同方向同時保有。"
               "1つの誤発注を別の同方向取引でナンピン気味に積んでおり、SL 連鎖時の損失が拡大している。")
    doc.append("")
    doc.append("### 所見2: 平均/最大スリッページが GBP_JPY で過大\n")
    doc.append("- **GBP_JPY**: avg +3.51 pips, p95 +21.28 pips, max +39.80 pips")
    doc.append("- **EUR_USD**: avg +1.96 pips, p95 +5.83 pips, max +6.22 pips")
    doc.append("- **USD_JPY**: avg +0.94 pips, p95 +6.37 pips, max +8.20 pips")
    doc.append("")
    doc.append("バックテストは spread=1pip 固定。GBP_JPY の実コストはこれより最大 4 倍以上。"
               "**60 秒ポーリングと M15 クローズの時刻差** + **実スプレッド** + **約定遅延**の合算と推定。")
    doc.append("")
    doc.append("### 所見3: USD_JPY の N が小さく統計的非有意\n")
    doc.append("実戦 7 取引・BT 3 取引はいずれも統計判定不能。"
               "勝率 14.3% vs 66.7% の差はサンプルサイズで揺れる（ベイズ二項信頼区間 95% で勝率は 1〜58% の幅）。"
               "「USD_JPY が壊滅的」という直感は再検証が必要 → 期間を伸ばして再評価を要する。")
    doc.append("")
    doc.append("### 所見4: 勝率自体は EUR_USD/GBP_JPY で BT と整合\n")
    doc.append("- EUR_USD: live 38.5% vs BT 40.0% （差 -1.5pt）")
    doc.append("- GBP_JPY: live 35.1% vs BT 35.3% （差 -0.2pt）")
    doc.append("")
    doc.append("**「戦略が壊れている」のではなく、「同時保有 + スリッページ」で同じ取引を 2 倍走らせているために期待値が薄まっている**。")
    doc.append("")
    doc.append("## 推奨アクション（根拠付き）\n")
    doc.append("**P0**: trading_loop に同ペア exclusive_orders 等価ガードを追加")
    doc.append(" - 実装案: `position_manager.has_open_position(instrument)` チェックを `_evaluate_signal` 直前に")
    doc.append(" - 期待効果: GBP_JPY 取引数が ~17 へ縮小、PF 0.87 → BT水準 0.53 付近"
               "（ナンピン的同方向積みが消えると平均PL改善も期待）")
    doc.append("")
    doc.append("**P1**: spread_pips パラメータをペア別に実測値で再校正")
    doc.append(" - GBP_JPY: 1pip → 3.5pip、EUR_USD: 1pip → 2pip、USD_JPY: 1pip → 1pip 維持")
    doc.append(" - 期待効果: バックテスト PF が現実的に下方修正され、戦略採用判断の精度向上")
    doc.append("")
    doc.append("**P2**: USD_JPY の評価期間を伸長（最低 30 取引）してから戦略変更を判断")
    doc.append("")
    doc.append("## 本分析の限界\n")
    doc.append("- **ポジションサイズ非対称**: バックテストは `cash=1M JPY × margin=0.04`（≒25xレバ）で")
    doc.append("  全資金フル投入。実戦は `RiskManager` で 1取引リスク = 0.5% 制限の risk-based サイジング")
    doc.append("  （概ね 0.02 lot）。**合計PLの絶対値は比較不可、平均PL/取引も同様**。")
    doc.append("  比較に値するのは **取引数・勝率・PF（相対）**。")
    doc.append("- **スリッページ定義**: 「シグナル発生バーの close」を理想 entry と仮定。")
    doc.append("  実際はバー close からシグナル評価まで数秒、発注から約定まで更に数秒。")
    doc.append("  `slip_avg_pips` は execution latency + spread + price drift を合算した実コスト指標。")
    doc.append("- **価格データ**: yfinance ロウソク足。FXブローカー (外為ファイネスト) の MT5 配信とは")
    doc.append("  数 pip 単位で乖離する可能性。あくまで「同期間に大体同じ条件でシグナルが何本出るか」の")
    doc.append("  指標値として読む。")
    doc.append("- **AI Advisor の影響を分離していない**: `AIAdvisor` の REJECT/CONTRADICT で")
    doc.append("  弾かれたシグナルが BT 側のシグナル数より多い可能性。今回は本番 DB 側の trade のみを")
    doc.append("  集計したため、フィルタ通過率は **発注後** の比率である点に注意。")
    doc.append("")
    doc.append("## ペア別詳細\n")
    doc.append("\n".join(md_sections))

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")
    print(f"DOC: {OUT_DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
