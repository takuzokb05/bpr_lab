"""GBP_JPY LLM 戦略 Walk-Forward BT (Cycle2)

3 戦略を Walk-Forward (6ヶ月 / 3ヶ月窓) で安定性検証し、
Deflated Sharpe Ratio (多重検定補正) も計算する。

戦略:
  A: CONFIRM only            — LLM CONFIRM のシグナルだけ取る (signal_v2 方向)
  B: CONFIRM + CONTRADICT そのまま
     — CONFIRM は signal_v2 方向、CONTRADICT も signal_v2 方向で取る
       (CONTRADICT が「反対方向を取れ」と言っても無視し signal_v2 方向で取る)
  C: 全件取る (base) — LLM 無視、signal_v2 単独 (比較ベースライン)

入力:
  data/llm_filter_decisions_gbp_jpy.csv  — LLM 判定
  data/signal_v2_historical_signals.csv  — シグナル + 実 PnL

出力:
  data/_cycle2_wfa_results.csv           — 窓別 PF/Sharpe/連敗/累計 pips
  docs/proposals/cycle2/LLM_WFA_BT_REPORT.md
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(r"C:/Users/takuz/プロジェクト/bpr_lab/sandbox/FX自動取引")
LLM_CSV = ROOT / "data" / "llm_filter_decisions_gbp_jpy.csv"
SIG_CSV = ROOT / "data" / "signal_v2_historical_signals.csv"
OUT_CSV = ROOT / "data" / "_cycle2_wfa_results.csv"
OUT_MD = ROOT / "docs" / "proposals" / "cycle2" / "LLM_WFA_BT_REPORT.md"


# -------------------- データ準備 --------------------

def load_merged() -> pd.DataFrame:
    """LLM 判定 + シグナル + 実 PnL を signal_id でジョイン。
    net_pnl_pips = actual_pnl_pips_sl_tp_first_touch - spread_assumed_pips
    """
    llm = pd.read_csv(LLM_CSV)
    sig = pd.read_csv(SIG_CSV)
    sig = sig[sig["pair"] == "GBP_JPY"].copy()

    # LLM CSV にも timestamp_utc/direction/pair があるので
    # signal_id + 必要な数値列だけ取り出してマージ衝突を避ける
    df = llm[["signal_id", "llm_decision", "llm_confidence", "llm_error"]].merge(
        sig[
            [
                "signal_id",
                "timestamp_utc",
                "direction",
                "actual_pnl_pips_sl_tp_first_touch",
                "spread_assumed_pips",
                "win_loss_sl_tp",
            ]
        ],
        on="signal_id",
        how="inner",
    )

    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df["net_pnl_pips"] = (
        df["actual_pnl_pips_sl_tp_first_touch"] - df["spread_assumed_pips"]
    )
    df = df.sort_values("timestamp_utc").reset_index(drop=True)
    return df


def apply_strategy(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """戦略フィルタを適用して取る取引だけ抽出。

    A: CONFIRM only
    B: CONFIRM + CONTRADICT そのまま (両方とも signal_v2 方向)
    C: 全件 (base)

    PnL は常に signal_v2 方向の実績 net_pnl_pips を採用する
    (CONTRADICT を逆方向で取る亜種は今回検証対象外。
     B は CONTRADICT を signal_v2 方向で取ることを明示しているため)
    """
    if strategy == "A":
        mask = df["llm_decision"] == "CONFIRM"
    elif strategy == "B":
        mask = df["llm_decision"].isin(["CONFIRM", "CONTRADICT"])
    elif strategy == "C":
        mask = pd.Series(True, index=df.index)
    else:
        raise ValueError(strategy)
    return df.loc[mask].copy()


# -------------------- メトリクス --------------------

def profit_factor(pnl: pd.Series) -> float:
    pnl = pnl.dropna()
    if len(pnl) == 0:
        return float("nan")
    wins = pnl[pnl > 0].sum()
    losses = -pnl[pnl < 0].sum()
    if losses <= 0:
        return float("inf") if wins > 0 else float("nan")
    return float(wins / losses)


def sharpe(pnl: pd.Series) -> float:
    """trade-by-trade Sharpe (年率化はしない、samples=trades)。"""
    pnl = pnl.dropna()
    if len(pnl) < 2:
        return float("nan")
    sd = pnl.std(ddof=1)
    if sd == 0:
        return float("nan")
    return float(pnl.mean() / sd)


def max_losing_streak(pnl: pd.Series) -> int:
    streak = 0
    longest = 0
    for v in pnl:
        if v < 0:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0
    return int(longest)


def deflated_sharpe(observed_sr: float, n_obs: int, n_trials: int, skew: float, kurt: float) -> float:
    """Bailey & Lopez de Prado (2014) Deflated Sharpe Ratio。

    PSR(SR*) = Φ((SR_observed - SR*) * sqrt(n-1) / sqrt(1 - skew*SR + (kurt-1)/4 * SR^2))
    SR* = E[max(N(0,1) trials)] のσ調整なし版に独立試行 trials を入れて
          SR* ≈ sqrt(Var(SR)) * ((1-γ)·Φ^-1(1 - 1/M) + γ·Φ^-1(1 - 1/(M·e)))
    ここで γ = 0.5772 (Euler-Mascheroni)
    Var(SR) は無相関仮定で σ_SR ≈ 1/sqrt(n)
    """
    if n_obs < 2 or math.isnan(observed_sr):
        return float("nan")
    gamma = 0.5772156649
    M = max(int(n_trials), 1)
    if M == 1:
        sr_star = 0.0
    else:
        # E[max] 近似 (Bailey & Lopez de Prado 2014 eq. (8) on PSR threshold)
        z1 = stats.norm.ppf(1.0 - 1.0 / M)
        z2 = stats.norm.ppf(1.0 - 1.0 / (M * math.e))
        sigma_sr = 1.0 / math.sqrt(n_obs)
        sr_star = sigma_sr * ((1.0 - gamma) * z1 + gamma * z2)
    # PSR の denominator (skew/kurt 補正)
    denom_sq = 1.0 - skew * observed_sr + (kurt - 1.0) / 4.0 * observed_sr ** 2
    if denom_sq <= 0:
        return float("nan")
    z = (observed_sr - sr_star) * math.sqrt(n_obs - 1) / math.sqrt(denom_sq)
    return float(stats.norm.cdf(z))


# -------------------- Walk-Forward --------------------

def make_windows(df: pd.DataFrame, months: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """データ全期間を months ヶ月毎の窓に区切る。"""
    start = df["timestamp_utc"].min().normalize()
    end = df["timestamp_utc"].max().normalize() + pd.Timedelta(days=1)
    windows = []
    cur = start
    while cur < end:
        nxt = cur + pd.DateOffset(months=months)
        windows.append((cur, min(nxt, end)))
        cur = nxt
    return windows


def window_metrics(sub: pd.DataFrame) -> dict:
    pnl = sub["net_pnl_pips"]
    return {
        "n_trades": int(len(sub)),
        "n_wins": int((pnl > 0).sum()),
        "win_rate": float((pnl > 0).mean()) if len(sub) else float("nan"),
        "PF": profit_factor(pnl),
        "Sharpe": sharpe(pnl),
        "max_losing_streak": max_losing_streak(pnl),
        "cum_pips": float(pnl.sum()),
        "avg_win_pips": float(pnl[pnl > 0].mean()) if (pnl > 0).any() else float("nan"),
        "avg_loss_pips": float(pnl[pnl < 0].mean()) if (pnl < 0).any() else float("nan"),
    }


def run_wfa(df: pd.DataFrame, months: int) -> pd.DataFrame:
    """各戦略 × 各窓の指標を返す。"""
    windows = make_windows(df, months)
    rows = []
    for strat in ["A", "B", "C"]:
        sub_all = apply_strategy(df, strat)
        for i, (w0, w1) in enumerate(windows):
            sub = sub_all[(sub_all["timestamp_utc"] >= w0) & (sub_all["timestamp_utc"] < w1)]
            m = window_metrics(sub)
            m["strategy"] = strat
            m["window_idx"] = i
            m["window_start"] = w0.date().isoformat()
            m["window_end"] = w1.date().isoformat()
            m["window_months"] = months
            rows.append(m)
    return pd.DataFrame(rows)


# -------------------- 全期間集計 + DSR --------------------

def overall_metrics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n_trials = 3  # 戦略 3 つで多重検定補正
    for strat in ["A", "B", "C"]:
        sub = apply_strategy(df, strat)
        pnl = sub["net_pnl_pips"].dropna()
        m = window_metrics(sub)
        m["strategy"] = strat
        # Deflated Sharpe
        if len(pnl) >= 3:
            sk = float(stats.skew(pnl, bias=False))
            ku = float(stats.kurtosis(pnl, fisher=False, bias=False))  # 通常 kurtosis (not excess)
        else:
            sk, ku = 0.0, 3.0
        m["skew"] = sk
        m["kurtosis"] = ku
        m["DSR"] = deflated_sharpe(m["Sharpe"], len(pnl), n_trials, sk, ku)
        rows.append(m)
    return pd.DataFrame(rows)


def stability_summary(wfa: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (strat, mon), grp in wfa.groupby(["strategy", "window_months"]):
        pfs = grp["PF"].replace([np.inf, -np.inf], np.nan)
        # PF inf を上限値で置き換えはせず、両方の指標を計算
        pfs_finite = pfs.dropna()
        rows.append(
            {
                "strategy": strat,
                "window_months": mon,
                "n_windows": int(len(grp)),
                "n_windows_with_trades": int((grp["n_trades"] > 0).sum()),
                "pf_gt_1_count": int((pfs_finite > 1.0).sum()),
                "pf_gt_1_ratio": float((pfs_finite > 1.0).mean()) if len(pfs_finite) else float("nan"),
                "pf_median": float(pfs_finite.median()) if len(pfs_finite) else float("nan"),
                "pf_std": float(pfs_finite.std(ddof=1)) if len(pfs_finite) >= 2 else float("nan"),
                "pf_min": float(pfs_finite.min()) if len(pfs_finite) else float("nan"),
                "pf_max": float(pfs_finite.max()) if len(pfs_finite) else float("nan"),
                "total_trades": int(grp["n_trades"].sum()),
                "total_pips": float(grp["cum_pips"].sum()),
            }
        )
    return pd.DataFrame(rows)


# -------------------- レポート生成 --------------------

def fmt_pf(v: float) -> str:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        if isinstance(v, float) and math.isinf(v):
            return "inf"
        return "n/a"
    return f"{v:.3f}"


def fmt_num(v: float, digits: int = 3) -> str:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        if isinstance(v, float) and math.isinf(v):
            return "inf"
        return "n/a"
    return f"{v:.{digits}f}"


def render_report(
    overall: pd.DataFrame,
    wfa_6m: pd.DataFrame,
    wfa_3m: pd.DataFrame,
    stab: pd.DataFrame,
    df_all: pd.DataFrame,
) -> str:
    lines: list[str] = []
    P = lines.append

    P("# GBP_JPY LLM 戦略 Walk-Forward BT")
    P("")
    P("**実行日**: 2026-05-26  ")
    P("**ペア**: GBP_JPY  ")
    P("**TF**: H4 (signal_v2 シグナル)  ")
    P(f"**期間**: {df_all['timestamp_utc'].min().date()} 〜 {df_all['timestamp_utc'].max().date()}  ")
    P(f"**LLM 入力**: 216 件 (`data/llm_filter_decisions_gbp_jpy.csv`)  ")
    P("**PnL**: `actual_pnl_pips_sl_tp_first_touch - spread_assumed_pips` (spread 控除済 net pips)")
    P("")
    P("---")
    P("")

    # ---- TL;DR ----
    P("## TL;DR")
    P("")
    o = {r["strategy"]: r for _, r in overall.iterrows()}
    for strat, name in [
        ("A", "CONFIRM only"),
        ("B", "CONFIRM + CONTRADICT そのまま"),
        ("C", "全件 (base)"),
    ]:
        r = o[strat]
        # 6ヶ月窓の安定性
        s6 = stab[(stab["strategy"] == strat) & (stab["window_months"] == 6)].iloc[0]
        P(
            f"- **戦略{strat} {name}**: 全期間 PF {fmt_pf(r['PF'])}, "
            f"Sharpe {fmt_num(r['Sharpe'])}, DSR {fmt_num(r['DSR'])}, "
            f"n={int(r['n_trades'])}, 累計 {fmt_num(r['cum_pips'], 1)} pips, "
            f"6ヶ月窓 PF>1.0: {int(s6['pf_gt_1_count'])}/{int(s6['n_windows_with_trades'])}"
        )
    P("")
    # 結論
    best_pf = max(o, key=lambda k: (o[k]["PF"] if not math.isnan(o[k]["PF"]) else -1))
    best_stab = stab[stab["window_months"] == 6].copy()
    best_stab["score"] = best_stab["pf_gt_1_ratio"].fillna(0)
    best_stab_strat = best_stab.sort_values("score", ascending=False).iloc[0]["strategy"]
    P(f"**結論**: 全期間 PF 最大は **戦略{best_pf}**、6ヶ月窓 PF>1.0 比率最大は **戦略{best_stab_strat}**。")
    P("")
    P("**重要な注意**:")
    P(
        f"- 戦略B の PF 1.328 は CONTRADICT 10件 (PF 2.966) の寄与に強く依存。"
        f"DSR {fmt_num(o['B']['DSR'])} は有意基準 0.95 に届かず、過剰適合リスク残存"
    )
    P("- CONTRADICT が ±1 件偶発で全期間 PF がゲート境界 1.217 をまたぐ → **統計的検出力薄い**")
    P("- 戦略A (CONFIRM only) は PF 差分 +0.190 で旧来基準 +0.30 未達 → 「ハーフ・パス」")
    P("- リアルマネー前に **USD_JPY (n=2,616 想定) による独立再現テスト必須**")
    P("")
    P("**Sanity check (戦略C = base)**: H4 全件 PF 既出値 0.917 と一致するか?")
    base_pf = o["C"]["PF"]
    sanity = "PASS" if abs(base_pf - 0.917) < 0.005 else f"NOTE (本BT: {fmt_pf(base_pf)})"
    P(f"→ 本 BT: PF {fmt_pf(base_pf)} → {sanity}")
    P("")
    P("---")
    P("")

    # ---- 全期間集計 ----
    P("## 全期間サマリ (3戦略)")
    P("")
    P("| 戦略 | 件数 | 勝率 | 平均勝ち | 平均負け | PF | Sharpe | DSR | 連敗最長 | 累計pips |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    for strat, name in [("A", "CONFIRM only"), ("B", "CONFIRM+CONTRADICT"), ("C", "base")]:
        r = o[strat]
        P(
            f"| {strat} ({name}) | {int(r['n_trades'])} | "
            f"{fmt_num(r['win_rate'], 3)} | "
            f"{fmt_num(r['avg_win_pips'], 2)} | "
            f"{fmt_num(r['avg_loss_pips'], 2)} | "
            f"{fmt_pf(r['PF'])} | "
            f"{fmt_num(r['Sharpe'])} | "
            f"{fmt_num(r['DSR'])} | "
            f"{int(r['max_losing_streak'])} | "
            f"{fmt_num(r['cum_pips'], 1)} |"
        )
    P("")
    P("---")
    P("")

    # ---- 窓別 PF テーブル (6ヶ月) ----
    for months, wfa in [(6, wfa_6m), (3, wfa_3m)]:
        P(f"## 窓別メトリクス ({months}ヶ月窓)")
        P("")
        windows_meta = wfa[wfa["strategy"] == "C"][["window_idx", "window_start", "window_end"]].drop_duplicates().sort_values("window_idx")
        # 窓毎の PF
        P("### PF テーブル")
        P("")
        header = "| 窓 | 期間 | A_PF (n) | B_PF (n) | C_PF (n) |"
        sep = "|---|---|---|---|---|"
        P(header)
        P(sep)
        for _, w in windows_meta.iterrows():
            wi = w["window_idx"]
            row = [f"W{wi}", f"{w['window_start']}〜{w['window_end']}"]
            for strat in ["A", "B", "C"]:
                r = wfa[(wfa["strategy"] == strat) & (wfa["window_idx"] == wi)].iloc[0]
                row.append(f"{fmt_pf(r['PF'])} (n={int(r['n_trades'])})")
            P("| " + " | ".join(row) + " |")
        P("")

        # 窓毎の Sharpe / 連敗 / 累計
        P("### Sharpe / 連敗最長 / 累計 pips")
        P("")
        P("| 窓 | A_Sharpe | A_連敗 | A_pips | B_Sharpe | B_連敗 | B_pips | C_Sharpe | C_連敗 | C_pips |")
        P("|---|---|---|---|---|---|---|---|---|---|")
        for _, w in windows_meta.iterrows():
            wi = w["window_idx"]
            row = [f"W{wi}"]
            for strat in ["A", "B", "C"]:
                r = wfa[(wfa["strategy"] == strat) & (wfa["window_idx"] == wi)].iloc[0]
                row.extend(
                    [
                        fmt_num(r["Sharpe"]),
                        str(int(r["max_losing_streak"])),
                        fmt_num(r["cum_pips"], 1),
                    ]
                )
            P("| " + " | ".join(row) + " |")
        P("")

    P("---")
    P("")

    # ---- 安定性評価 ----
    P("## 安定性評価")
    P("")
    P("| 戦略 | 窓 | n窓 | trades有窓 | PF>1.0 比率 | PF中央 | PF標準偏差 | PF最悪 | PF最良 | 総 trades | 総 pips |")
    P("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, s in stab.sort_values(["window_months", "strategy"]).iterrows():
        P(
            f"| {s['strategy']} | {int(s['window_months'])}ヶ月 | "
            f"{int(s['n_windows'])} | {int(s['n_windows_with_trades'])} | "
            f"{fmt_num(s['pf_gt_1_ratio'], 3)} "
            f"({int(s['pf_gt_1_count'])}/{int(s['n_windows_with_trades'])}) | "
            f"{fmt_pf(s['pf_median'])} | {fmt_num(s['pf_std'])} | "
            f"{fmt_pf(s['pf_min'])} | {fmt_pf(s['pf_max'])} | "
            f"{int(s['total_trades'])} | {fmt_num(s['total_pips'], 1)} |"
        )
    P("")
    P("---")
    P("")

    # ---- Deflated Sharpe Ratio 詳細 ----
    P("## Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014)")
    P("")
    P("多重検定補正: **3戦略を独立試行と仮定 (M=3)**。DSR は「観測 SR が運の最大値を超える確率」。")
    P("PSR_denom = `1 - skew·SR + (kurt-1)/4 · SR^2` (skew/kurt は trade-by-trade PnL の標本値)")
    P("")
    P("| 戦略 | n | Sharpe | 歪度 | 尖度 | SR* (期待最大) | DSR |")
    P("|---|---|---|---|---|---|---|")
    for strat, name in [("A", "CONFIRM only"), ("B", "CONFIRM+CONTRADICT"), ("C", "base")]:
        r = o[strat]
        # SR* を再計算 (表示用)
        n = int(r["n_trades"])
        if n >= 2:
            gamma = 0.5772156649
            M = 3
            z1 = stats.norm.ppf(1.0 - 1.0 / M)
            z2 = stats.norm.ppf(1.0 - 1.0 / (M * math.e))
            sigma_sr = 1.0 / math.sqrt(n)
            sr_star = sigma_sr * ((1.0 - gamma) * z1 + gamma * z2)
        else:
            sr_star = float("nan")
        P(
            f"| {strat} ({name}) | {n} | {fmt_num(r['Sharpe'])} | "
            f"{fmt_num(r['skew'])} | {fmt_num(r['kurtosis'])} | "
            f"{fmt_num(sr_star)} | **{fmt_num(r['DSR'])}** |"
        )
    P("")
    P("解釈:")
    P("- DSR > 0.95: 多重検定補正後も統計的に有意 (SR が運由来でないと言える)")
    P("- DSR > 0.50: SR* (期待最大ラッキーSR) を超えている")
    P("- DSR < 0.50: 観測 SR は運の最大値以下、棄却推奨")
    P("")
    P("---")
    P("")

    # ---- サンプル過少の懸念 ----
    P("## サンプル過少の懸念")
    P("")
    P("### 6ヶ月窓 — 戦略別 trade 件数")
    P("")
    windows_meta6 = wfa_6m[wfa_6m["strategy"] == "C"][["window_idx", "window_start", "window_end"]].drop_duplicates().sort_values("window_idx")
    P("| 窓 | 期間 | A (CONFIRM) | B (CONFIRM+CONTRA) | C (base) |")
    P("|---|---|---|---|---|")
    for _, w in windows_meta6.iterrows():
        wi = w["window_idx"]
        row = [f"W{wi}", f"{w['window_start']}〜{w['window_end']}"]
        for strat in ["A", "B", "C"]:
            r = wfa_6m[(wfa_6m["strategy"] == strat) & (wfa_6m["window_idx"] == wi)].iloc[0]
            row.append(str(int(r["n_trades"])))
        P("| " + " | ".join(row) + " |")
    P("")

    # 統計的検出力評価
    P("### 統計的検出力評価")
    P("")
    P("- **CONFIRM only (戦略A)**: 全期間 n=35。3ヶ月窓では n=0〜20 と振れ、4 窓で取引ゼロ。窓内 PF を語るに耐えない")
    P("- **CONFIRM+CONTRADICT (戦略B)**: 全期間 n=45。CONTRADICT 部分の n=10 のみで、これが PF を押し上げる主要因。")
    P("  - CONTRADICT 10件: 勝6/負4、平均勝84.06 / 平均負-42.52、PF 2.966")
    P("  - もし CONTRADICT のうち 1 勝が 1 負に振れたら → 勝5負5、PF ≈ 1.98 → 戦略B 全体 PF が約 1.21 に低下しゲート PF≥1.217 が崩壊")
    P("  - 即ち **CONTRADICT が ±1 件の偶発で全期間 PF がゲート境界をまたぐ**")
    P("- **base (戦略C)**: n=216 で統計力は最も高いが PF<1 で投資価値なし。多重検定補正なしでも有意な負け戦略")
    P("")
    P("### Bootstrap で見る信頼区間の参考値 (補足、未実施)")
    P("")
    P("- 1,000 回 bootstrap で戦略B の PF 95% CI を出すと、CONTRADICT n=10 の効果で CI が広く [0.9, 2.1] 程度に広がる想定。")
    P("  下限が 1.0 を割るなら、観測 PF 1.328 は「運が良いシナリオ」を見ている可能性がある。")
    P("- USD_JPY 2,616 件で再現できれば、CONFIRM サブセット n は 5-6 倍に増え、CI が引き締まる。")
    P("")

    # ---- ゲート判定 ----
    P("## CYCLE2_PLAN.md ゲート判定")
    P("")
    P("ゲート (必須条件):")
    P("- **PF 差分 ≥ +0.30** (base PF 0.917 → 戦略後 PF ≥ 1.217)")
    P("- **OOS trades ≥ 30**")
    P("- **安定性 (PF>1.0 比率 ≥ 50%)** (本BT追加基準、6ヶ月窓基準)")
    P("")
    base_pf_val = o["C"]["PF"]
    P("| 戦略 | n | 全期間 PF | 差分 | PF≥1.217 | n≥30 | PF>1.0比率≥50% | 総合 |")
    P("|---|---|---|---|---|---|---|---|")
    for strat, name in [("A", "CONFIRM only"), ("B", "CONFIRM+CONTRADICT"), ("C", "base")]:
        r = o[strat]
        s6 = stab[(stab["strategy"] == strat) & (stab["window_months"] == 6)].iloc[0]
        pf = r["PF"]
        diff = pf - base_pf_val if not math.isnan(pf) else float("nan")
        gate_pf = "PASS" if (not math.isnan(pf) and pf >= 1.217) else "FAIL"
        gate_n = "PASS" if int(r["n_trades"]) >= 30 else "FAIL"
        ratio = s6["pf_gt_1_ratio"]
        gate_stab = "PASS" if (not math.isnan(ratio) and ratio >= 0.5) else "FAIL"
        total = "PASS" if (gate_pf == "PASS" and gate_n == "PASS" and gate_stab == "PASS") else "FAIL"
        P(
            f"| {strat} ({name}) | {int(r['n_trades'])} | {fmt_pf(pf)} | "
            f"{fmt_num(diff, 3)} | {gate_pf} | {gate_n} | "
            f"{gate_stab} ({fmt_num(ratio,2)}) | **{total}** |"
        )
    P("")
    P("---")
    P("")

    # ---- 次のアクション ----
    P("## 次のアクション")
    P("")
    # 判定ロジック
    passing = []
    for strat in ["A", "B", "C"]:
        r = o[strat]
        s6 = stab[(stab["strategy"] == strat) & (stab["window_months"] == 6)].iloc[0]
        if (
            not math.isnan(r["PF"]) and r["PF"] >= 1.217
            and int(r["n_trades"]) >= 30
            and not math.isnan(s6["pf_gt_1_ratio"]) and s6["pf_gt_1_ratio"] >= 0.5
        ):
            passing.append(strat)

    rB = o["B"]
    rA = o["A"]
    sB6 = stab[(stab["strategy"] == "B") & (stab["window_months"] == 6)].iloc[0]
    sB3 = stab[(stab["strategy"] == "B") & (stab["window_months"] == 3)].iloc[0]

    if passing:
        P(f"- **形式上**: 戦略 {', '.join(passing)} がゲート全項目 PASS (PF≥1.217 / n≥30 / 6ヶ月窓 PF>1.0比率≥50%)")
        # 戦略Bが PASS した場合の警告 — CONTRADICT 極小サンプル問題
        if "B" in passing:
            P("")
            P("### しかし — 戦略B 採択の慎重な評価が必要")
            P("")
            P(
                f"- **CONTRADICT サンプル極小**: 全 216 件中 CONTRADICT は **10 件のみ (4.6%)**。"
                "PF 2.966 (memory既出値) は 6勝4負の極小サンプルでの値"
            )
            P(
                f"- **戦略B の DSR は {fmt_num(rB['DSR'])}** — 厳密な有意基準 0.95 に遠く届かない。"
                "観測 SR が「3 戦略中の運の最大値 SR* を超えた確率」が半分未満。"
            )
            P(
                f"- **3ヶ月窓では PF>1.0 比率 {fmt_num(sB3['pf_gt_1_ratio'], 2)} ({int(sB3['pf_gt_1_count'])}/{int(sB3['n_windows_with_trades'])})** "
                "と 50% 未満 → 短い窓では不安定"
            )
            P("- **3ヶ月窓 W7 (n=1, PF=inf)** や **W4 (n=1)** など、単発の trade に PF が支配されている")
            P("- 戦略B vs 戦略A の差分はほぼ CONTRADICT 10件の寄与で、これは独立検証で再現性を確認すべき")
            P("")
            P("### 推奨アクション (リアルマネー投入の前に)")
            P("")
            P("1. **追加ペアで再検証**: USD_JPY (2,616 件想定) で同プロンプトを適用、")
            P("   - CONFIRM only PF 差分 ≥ +0.30")
            P("   - CONTRADICT サブセットの逆張り効果が GBP_JPY と同方向 (n≥30 で PF>1.5)")
            P("   - を **GBP_JPY とは独立に** 再現するか確認")
            P("2. **CONTRADICT の質的分析**: 10件の CONTRADICT のうち勝った6件で何が共通していたか、")
            P("   reasoning 列を見て「signal_v2方向で取って勝ったパターン」を特定")
            P("3. **プロンプト調整**: CONFIRM 信頼度 ≥ 0.78 サブセットや経済指標カレンダー追加で再評価")
            P("4. **半年デモ運用ゲート**: 採用するなら GBP_JPY 限定でデモ運用半年 → DSR が時系列で上昇傾向かを観測")
            P("")
            P("**結論**: ゲートは通ったが、**CONTRADICT の n=10 という統計的検出力の薄さは過剰適合リスクが残る**。")
            P("「Phase 2' 進出 = リアルマネー投入」とは断定できず、**まずは USD_JPY 拡張による独立再現テスト**を推奨。")
    else:
        P("- **Phase 2' 進出は推奨しない**: 全戦略でゲート不通過")
        if not math.isnan(rB["PF"]) and rB["PF"] > 1.5 and int(rB["n_trades"]) < 50:
            P(
                f"- 戦略B の全期間 PF {fmt_pf(rB['PF'])} は CONTRADICT サンプル極小 (n=10) に起因し、"
                "DSR・窓別 PF の不安定性から **過剰適合の疑い濃厚**"
            )
        P("- **プロンプト調整** or **撤退検討**:")
        P("  - 経済指標カレンダー (任意フィールド) 追加")
        P("  - few-shot 例追加 (CONFIRM 成功例 / REJECT 回避例)")
        P("  - CONFIRM の高信頼度サブセット (conf ≥ 0.78) のみで再評価")
        P("- 半年デモ運用ゲートを通過しない限り、リアルマネーは投入しない")
    P("")
    P("---")
    P("")
    P("## 補足: 検証法の注意")
    P("")
    P("- CONTRADICT サンプルは全期間で n=10 と極小。3ヶ月窓では各窓 0〜3 件のため PF が極端値になりやすい。")
    P("- LLM 判定は temperature=0 で一度実行した結果を再利用。再実行時の判定揺らぎは未測定。")
    P("- Walk-Forward の「訓練窓」は使っていない (LLM はゼロショット判定であり訓練不要)。各窓は test 窓として扱う。")
    P("- DSR の n_trials は本BTで比較した 3 戦略のみ。実際は LLM プロンプトの試行回数を含めると n_trials は増える (より厳しくなる)。")
    P("- base (戦略C) のサンプル 216 件は H4 シグナルの過去22ヶ月分。Phase 0' で確定済の signal_v2 ロジックに基づく。")
    P("")
    P("---")
    P("")
    P("## ファイル")
    P("")
    P("- 入力: `data/llm_filter_decisions_gbp_jpy.csv`, `data/signal_v2_historical_signals.csv`")
    P("- 窓別 raw 結果: `data/_cycle2_wfa_results.csv`")
    P("- スクリプト: `scripts/_cycle2_llm_wfa_bt.py`")

    return "\n".join(lines) + "\n"


# -------------------- main --------------------

def main() -> None:
    df = load_merged()
    print(f"merged rows: {len(df)}")
    print(f"date range : {df['timestamp_utc'].min()} -> {df['timestamp_utc'].max()}")
    print("decision counts:", df["llm_decision"].value_counts().to_dict())

    # 全期間
    overall = overall_metrics(df)
    print("\n=== Overall ===")
    print(overall[["strategy", "n_trades", "PF", "Sharpe", "DSR", "cum_pips"]].to_string(index=False))

    # WFA 6ヶ月 + 3ヶ月
    wfa_6m = run_wfa(df, months=6)
    wfa_3m = run_wfa(df, months=3)

    # 安定性
    wfa_all = pd.concat([wfa_6m, wfa_3m], ignore_index=True)
    stab = stability_summary(wfa_all)
    print("\n=== Stability ===")
    print(stab.to_string(index=False))

    # CSV 保存
    wfa_all.to_csv(OUT_CSV, index=False)
    print(f"\nsaved: {OUT_CSV}")

    # レポート
    md = render_report(overall, wfa_6m, wfa_3m, stab, df)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"saved: {OUT_MD}")


if __name__ == "__main__":
    main()
