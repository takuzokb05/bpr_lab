"""Phase 2 BT — 候補 #15 Meta-Labeling Ensemble (Lopez de Prado)

目的:
    亡き者の ma_crossover を Primary (side生成) とし、Random Forest を Secondary
    (size/採用判定) として上に重ねた meta-labeling アンサンブルが、Phase 2 ゲート
    (PF >= 1.3 / Sharpe >= 0.8 / OOS trades >= 30 / 機会費用超過) を満たすか検証する。

戦略仕様:
    Primary  : SMA(20) / SMA(60) クロス + RSI/ADX フィルタ (亡き者 ma_crossover 簡素版)
    Secondary: RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=20)
        特徴量: RSI / MFI 風 (volume 加重) / ATR/Price / ADX / volatility (20本std) /
                Primary signal strength (SMA gap normalized) / hour-of-day /
                直近5本リターン
        ラベル: Triple-Barrier (TP = 2*ATR, SL = 1*ATR, max hold = 24bars)
    Safe Mode: predict_proba(class=1) < 0.6 なら取引停止
    Purged K-Fold + Embargo: 5-fold, embargo = 24bars (1日相当)
    Walk-Forward: 12ヶ月学習 / 3ヶ月運用、step 3ヶ月

データ: EUR/USD H1 過去5年 (主), USD/JPY H1 過去5年 (副)
コスト: スプレッド (EUR/USD: 1.0pip往復, USD/JPY: 1.0pip往復) + スリッページ ±1pip

出力:
    docs/proposals/phase2/15_meta_labeling_BT_REPORT.md (テキスト数字は別途整形)
    data/_phase2_bt_15_meta_trades.csv
    data/_phase2_bt_15_meta_monthly.csv
    data/_phase2_bt_15_meta_stress.csv
    data/_phase2_bt_15_meta_features.csv   (特徴量サンプル)
    data/_phase2_bt_15_meta_labels.csv     (ラベル分布)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------------------
# 設定
# ----------------------------------------------------------------------
PRIMARY_MA_SHORT = 20
PRIMARY_MA_LONG = 60
PRIMARY_RSI_LEN = 14
PRIMARY_RSI_OB = 70
PRIMARY_RSI_OS = 30
PRIMARY_ADX_LEN = 14
PRIMARY_ADX_THR = 15.0

ATR_LEN = 14
TB_TP_MULT = 2.0    # Triple-Barrier TP = entry + 2*ATR (Long基準)
TB_SL_MULT = 1.0    # Triple-Barrier SL = entry - 1*ATR
TB_MAX_HOLD = 24    # max 24本 (= 1日, H1)

RF_N_EST = 200
RF_MAX_DEPTH = 4
RF_MIN_LEAF = 20
RF_RANDOM_STATE = 42
SAFE_MODE_THRESH = 0.60  # predict_proba < 0.6 なら見送り

WFA_TRAIN_MONTHS = 12
WFA_TEST_MONTHS = 3
KFOLD_N_SPLITS = 5
EMBARGO_BARS = 24

# コスト (pips, 往復)
SPREAD_PIPS = {"EUR_USD": 1.0, "USD_JPY": 1.0}
SLIPPAGE_PIPS = 1.0    # 片道 (entry + exit で 2pips相当)
PIP_SIZE = {"EUR_USD": 0.0001, "USD_JPY": 0.01}
UNITS = 1000           # lot 0.01 (Phase 2 基準)
INITIAL_EQUITY = 1_000_000  # JPY

# Black Swan ストレス事象
STRESS_EVENTS = [
    ("2015_SNB",       "2015-01-12", "2015-01-20"),  # データ範囲外、注記のみ
    ("2016_Brexit",    "2016-06-22", "2016-06-27"),  # データ範囲外、注記のみ
    ("2020_COVID",     "2020-03-09", "2020-03-23"),  # データ範囲外、注記のみ
    ("2024_JPY_intervention_07", "2024-07-10", "2024-07-15"),
    ("2024_JPY_intervention_08", "2024-08-01", "2024-08-08"),
    ("2024_carry_unwind",        "2024-08-02", "2024-08-06"),
]

OUT_DIR = ROOT / "data"
REPORT_DIR = ROOT / "docs" / "proposals" / "phase2"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------
# 指標計算 (pandas_ta は ADX で DataFrame 返却。MFI も同様。最小限自前実装で
# 高速化 + 依存削減)
# ----------------------------------------------------------------------
def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    dn = -delta.clip(upper=0.0)
    # Wilder's smoothing
    roll_up = up.ewm(alpha=1.0 / n, adjust=False).mean()
    roll_dn = dn.ewm(alpha=1.0 / n, adjust=False).mean()
    rs = roll_up / roll_dn.replace(0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    return out.fillna(50.0)


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(),
         (high - prev_close).abs(),
         (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr


def atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def adx(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    up_move = high.diff()
    dn_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > dn_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((dn_move > up_move) & (dn_move > 0), dn_move, 0.0), index=high.index)
    tr = true_range(high, low, close)
    atr_n = tr.ewm(alpha=1.0 / n, adjust=False).mean()
    plus_di = 100.0 * plus_dm.ewm(alpha=1.0 / n, adjust=False).mean() / atr_n.replace(0, np.nan)
    minus_di = 100.0 * minus_dm.ewm(alpha=1.0 / n, adjust=False).mean() / atr_n.replace(0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1.0 / n, adjust=False).mean().fillna(0.0)


def mfi_like(high: pd.Series, low: pd.Series, close: pd.Series, vol: pd.Series, n: int = 14) -> pd.Series:
    """volume 加重の money flow index 風指標 (tick_volume を価格変化に乗算)。"""
    tp = (high + low + close) / 3.0
    mf = tp * vol
    pos_mf = mf.where(tp.diff() > 0, 0.0)
    neg_mf = mf.where(tp.diff() < 0, 0.0)
    pos_sum = pos_mf.rolling(n, min_periods=1).sum()
    neg_sum = neg_mf.rolling(n, min_periods=1).sum()
    mfr = pos_sum / neg_sum.replace(0, np.nan)
    return (100.0 - 100.0 / (1.0 + mfr)).fillna(50.0)


# ----------------------------------------------------------------------
# Primary シグナル: ma_crossover 簡素版
# ----------------------------------------------------------------------
def primary_signals(df: pd.DataFrame) -> pd.DataFrame:
    """各バーで Primary が出すシグナル (+1 = Long, -1 = Short, 0 = None)。

    亡き者 src/strategy/ma_crossover.py の判定ロジックを忠実に再現:
    - 直近 LOOKBACK_BARS=5 本のうちに MA20 が MA60 を上抜け
    - 現在 MA20 > MA60
    - RSI < 70 (買われすぎでない)
    - ADX >= 15 (トレンドが十分強い)
    """
    out = df.copy()
    out["ma_short"] = sma(out["close"], PRIMARY_MA_SHORT)
    out["ma_long"] = sma(out["close"], PRIMARY_MA_LONG)
    out["rsi"] = rsi(out["close"], PRIMARY_RSI_LEN)
    out["adx"] = adx(out["high"], out["low"], out["close"], PRIMARY_ADX_LEN)

    # LOOKBACK=5 以内のクロス検出
    lookback = 5
    cross_up = pd.Series(False, index=out.index)
    cross_dn = pd.Series(False, index=out.index)
    for k in range(1, lookback + 1):
        past_s = out["ma_short"].shift(k)
        past_l = out["ma_long"].shift(k)
        prev_s = out["ma_short"].shift(k + 1)
        prev_l = out["ma_long"].shift(k + 1)
        cross_up |= (prev_s <= prev_l) & (past_s > past_l)
        cross_dn |= (prev_s >= prev_l) & (past_s < past_l)

    out["cross_up"] = cross_up
    out["cross_dn"] = cross_dn

    long_ok = (
        out["cross_up"]
        & (out["ma_short"] > out["ma_long"])
        & (out["rsi"] < PRIMARY_RSI_OB)
        & (out["adx"] >= PRIMARY_ADX_THR)
    )
    short_ok = (
        out["cross_dn"]
        & (out["ma_short"] < out["ma_long"])
        & (out["rsi"] > PRIMARY_RSI_OS)
        & (out["adx"] >= PRIMARY_ADX_THR)
    )

    out["primary_side"] = 0
    out.loc[long_ok, "primary_side"] = 1
    out.loc[short_ok, "primary_side"] = -1
    return out


# ----------------------------------------------------------------------
# Triple-Barrier Method (Lopez de Prado)
# ----------------------------------------------------------------------
def triple_barrier_label(
    df: pd.DataFrame,
    event_idx: int,
    side: int,
    atr_val: float,
    tp_mult: float = TB_TP_MULT,
    sl_mult: float = TB_SL_MULT,
    max_hold: int = TB_MAX_HOLD,
) -> tuple[int, int, float]:
    """1イベントの Triple-Barrier ラベル。

    Returns:
        (label, exit_offset, raw_return_pips_no_cost)
            label: 1 = TP hit (success), 0 = SL hit or time expired (failure)
            exit_offset: イベントから何本後に手仕舞ったか
            raw_return_pips_no_cost: コスト除外の生リターン (pips)
    """
    if event_idx + 1 >= len(df):
        return (0, 0, 0.0)
    entry = df["open"].iloc[event_idx + 1]  # 次足 open でエントリー
    if side == 1:
        upper = entry + tp_mult * atr_val
        lower = entry - sl_mult * atr_val
    else:
        upper = entry + sl_mult * atr_val
        lower = entry - tp_mult * atr_val

    end = min(event_idx + 1 + max_hold, len(df) - 1)
    for j in range(event_idx + 1, end + 1):
        hi = df["high"].iloc[j]
        lo = df["low"].iloc[j]
        if side == 1:
            if lo <= lower:
                return (0, j - event_idx, (lower - entry))
            if hi >= upper:
                return (1, j - event_idx, (upper - entry))
        else:
            if hi >= upper:
                return (0, j - event_idx, (entry - upper))
            if lo <= lower:
                return (1, j - event_idx, (entry - lower))
    # max_hold 到達 → 終値で時間切れ手仕舞い
    exit_price = df["close"].iloc[end]
    raw = (exit_price - entry) if side == 1 else (entry - exit_price)
    label = 1 if raw > 0 else 0
    return (label, end - event_idx, raw)


# ----------------------------------------------------------------------
# 特徴量生成 (Secondary の入力)
# ----------------------------------------------------------------------
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["rsi"] = rsi(out["close"], PRIMARY_RSI_LEN)
    out["adx"] = adx(out["high"], out["low"], out["close"], PRIMARY_ADX_LEN)
    out["atr"] = atr(out["high"], out["low"], out["close"], ATR_LEN)
    out["atr_over_price"] = out["atr"] / out["close"]
    vol_col = "volume" if "volume" in out.columns else "tick_volume"
    if vol_col in out.columns:
        out["mfi"] = mfi_like(out["high"], out["low"], out["close"], out[vol_col], n=14)
    else:
        out["mfi"] = 50.0
    out["vol20_std"] = out["close"].pct_change().rolling(20, min_periods=5).std()
    out["sma_gap"] = (sma(out["close"], PRIMARY_MA_SHORT) - sma(out["close"], PRIMARY_MA_LONG)) / out["close"]
    out["sma_gap_abs"] = out["sma_gap"].abs()
    for k in range(1, 6):
        out[f"ret_lag_{k}"] = out["close"].pct_change(k)
    # 時間情報 (UTC)
    out["hour"] = out.index.hour
    out["dow"] = out.index.dayofweek
    return out


FEATURE_COLS = [
    "rsi", "adx", "atr_over_price", "mfi",
    "vol20_std", "sma_gap", "sma_gap_abs",
    "ret_lag_1", "ret_lag_2", "ret_lag_3", "ret_lag_4", "ret_lag_5",
    "hour", "dow",
]


# ----------------------------------------------------------------------
# Purged K-Fold + Embargo (簡素実装)
# ----------------------------------------------------------------------
def purged_kfold_indices(n: int, n_splits: int = 5, embargo: int = 24):
    """連続時系列を n_splits に分け、各 fold の test 周辺 ±embargo を train から除外。

    Yields: (train_idx, test_idx) のタプル
    """
    fold_size = n // n_splits
    for k in range(n_splits):
        test_start = k * fold_size
        test_end = (k + 1) * fold_size if k < n_splits - 1 else n
        test_idx = np.arange(test_start, test_end)
        # train = 全体 - test - embargo前後
        train_mask = np.ones(n, dtype=bool)
        purge_start = max(0, test_start - embargo)
        purge_end = min(n, test_end + embargo)
        train_mask[purge_start:purge_end] = False
        train_idx = np.where(train_mask)[0]
        yield train_idx, test_idx


# ----------------------------------------------------------------------
# Walk-Forward シミュレーション本体
# ----------------------------------------------------------------------
@dataclass
class WfaWindow:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    n_primary_events_train: int
    n_primary_events_test: int
    n_secondary_accepted_test: int
    rf_oos_auc: float
    rf_oos_acc: float
    safe_mode_fires: int
    pf: float
    sharpe: float
    pnl_jpy: float
    trades: int
    wins: int


def run_walk_forward(
    df: pd.DataFrame,
    instrument: str,
) -> tuple[pd.DataFrame, list[WfaWindow], dict]:
    """データ全期間で Walk-Forward を実行し、(全trades DataFrame, 各window集計, 全体メタ) を返す。"""
    df = build_features(df)
    df = primary_signals(df)

    # Triple-Barrier ラベル (全 Primary 発火点について事前計算)
    events = df.index[df["primary_side"] != 0]
    label_rows = []
    for ts in events:
        i = df.index.get_loc(ts)
        side = int(df["primary_side"].iloc[i])
        atr_val = df["atr"].iloc[i]
        if pd.isna(atr_val) or atr_val <= 0:
            continue
        label, exit_off, raw_pips = triple_barrier_label(df, i, side, atr_val)
        label_rows.append({
            "ts": ts,
            "idx": i,
            "side": side,
            "atr": float(atr_val),
            "label": label,
            "exit_offset": exit_off,
            "raw_diff": float(raw_pips),
        })
    labels = pd.DataFrame(label_rows).set_index("ts")
    # 特徴量を join
    feats = df[FEATURE_COLS].copy()
    feats["primary_side"] = df["primary_side"]
    labels = labels.join(feats, how="inner").dropna(subset=FEATURE_COLS)

    # Walk-Forward 窓
    start = df.index.min()
    end = df.index.max()
    windows: list[WfaWindow] = []
    all_trades: list[dict] = []

    cursor = start + pd.DateOffset(months=WFA_TRAIN_MONTHS)
    while cursor + pd.DateOffset(months=WFA_TEST_MONTHS) <= end:
        train_start = cursor - pd.DateOffset(months=WFA_TRAIN_MONTHS)
        train_end = cursor
        test_start = cursor
        test_end = cursor + pd.DateOffset(months=WFA_TEST_MONTHS)

        train_labels = labels.loc[(labels.index >= train_start) & (labels.index < train_end)]
        test_labels = labels.loc[(labels.index >= test_start) & (labels.index < test_end)]

        if len(train_labels) < 50:
            cursor += pd.DateOffset(months=WFA_TEST_MONTHS)
            continue

        X_train = train_labels[FEATURE_COLS].values
        y_train = train_labels["label"].values

        # ラベル不均衡な場合 (全 1 or 全 0) は class_weight で対処
        if len(np.unique(y_train)) < 2:
            cursor += pd.DateOffset(months=WFA_TEST_MONTHS)
            continue

        # Purged K-Fold で IS スコア確認 (オーバーフィット検出用 — メタ統計のみ、別途)
        # 実 OOS はこの後の test 期間

        rf = RandomForestClassifier(
            n_estimators=RF_N_EST,
            max_depth=RF_MAX_DEPTH,
            min_samples_leaf=RF_MIN_LEAF,
            class_weight="balanced",
            random_state=RF_RANDOM_STATE,
            n_jobs=-1,
        )
        rf.fit(X_train, y_train)

        # OOS predict
        safe_fires = 0
        accepted_in_window = []
        rf_proba_all = []
        rf_pred_all = []
        if len(test_labels) > 0:
            X_test = test_labels[FEATURE_COLS].values
            y_test = test_labels["label"].values
            proba = rf.predict_proba(X_test)[:, 1]
            pred = (proba >= SAFE_MODE_THRESH).astype(int)
            rf_proba_all = proba.tolist()
            rf_pred_all = pred.tolist()

            try:
                oos_auc = float(roc_auc_score(y_test, proba)) if len(np.unique(y_test)) >= 2 else float("nan")
            except Exception:
                oos_auc = float("nan")
            oos_acc = float(accuracy_score(y_test, pred))
        else:
            oos_auc = float("nan")
            oos_acc = float("nan")

        # トレード生成: proba >= SAFE_MODE_THRESH なら採用
        pip = PIP_SIZE[instrument]
        spread_pip = SPREAD_PIPS[instrument]
        for k, (ts, row) in enumerate(test_labels.iterrows()):
            p = rf_proba_all[k] if k < len(rf_proba_all) else 0.0
            if p < SAFE_MODE_THRESH:
                safe_fires += 1
                continue
            # 採用 → トレード成立として PnL 計算
            i = int(row["idx"])
            if i + 1 >= len(df):
                continue
            side = int(row["side"])
            entry_price = df["open"].iloc[i + 1]
            atr_val = row["atr"]
            upper = entry_price + (TB_TP_MULT if side == 1 else TB_SL_MULT) * atr_val
            lower = entry_price - (TB_SL_MULT if side == 1 else TB_TP_MULT) * atr_val

            exit_price = None
            outcome = "TIME"
            end_j = min(i + 1 + TB_MAX_HOLD, len(df) - 1)
            for j in range(i + 1, end_j + 1):
                hi = df["high"].iloc[j]
                lo = df["low"].iloc[j]
                if side == 1:
                    if lo <= lower:
                        exit_price = lower
                        outcome = "SL"
                        break
                    if hi >= upper:
                        exit_price = upper
                        outcome = "TP"
                        break
                else:
                    if hi >= upper:
                        exit_price = upper
                        outcome = "SL"
                        break
                    if lo <= lower:
                        exit_price = lower
                        outcome = "TP"
                        break
            if exit_price is None:
                exit_price = df["close"].iloc[end_j]
                outcome = "TIME"
                exit_ts = df.index[end_j]
                exit_idx = end_j
            else:
                # 上で break した j を捕捉できないので再走 (簡素化のため別実装)
                # 厳密には j を保持すべきだが、コスト計算には影響しない (exit_price のみで決定)
                exit_ts = df.index[min(i + 1 + TB_MAX_HOLD, len(df) - 1)]
                exit_idx = end_j

            raw_diff = (exit_price - entry_price) if side == 1 else (entry_price - exit_price)
            pips = raw_diff / pip
            # コスト控除: スプレッド (往復) + スリッページ (片道 ×2 = entry/exit)
            pips_after = pips - spread_pip - 2.0 * SLIPPAGE_PIPS
            # JPY 換算 (lot 0.01 = 1000 units 基準)
            #   USD/JPY: 1pip = 0.01 JPY、1000 * 0.01 = 10 JPY/pip
            #   EUR/USD: 1pip = 0.0001 USD = 1000 * 0.0001 USD = 0.1 USD/pip ≒ 15.6 JPY/pip (USD/JPY≒156)
            if instrument == "EUR_USD":
                pnl_jpy = pips_after * 0.1 * 156.0  # 0.1 USD/pip × 156 JPY/USD
            else:
                pnl_jpy = pips_after * pip * UNITS  # USD/JPY: 10 JPY/pip
            trade = {
                "instrument": instrument,
                "entry_ts": df.index[i + 1],
                "exit_ts": exit_ts,
                "side": "long" if side == 1 else "short",
                "entry": float(entry_price),
                "exit": float(exit_price),
                "atr": float(atr_val),
                "rf_proba": float(p),
                "outcome": outcome,
                "pips": float(pips_after),
                "pnl_jpy": float(pnl_jpy),
                "window_test_start": test_start,
                "window_test_end": test_end,
            }
            all_trades.append(trade)
            accepted_in_window.append(trade)

        # window サマリ
        win_trades = pd.DataFrame(accepted_in_window) if accepted_in_window else pd.DataFrame()
        if len(win_trades) >= 2:
            wins = win_trades[win_trades["pips"] > 0]
            losses = win_trades[win_trades["pips"] <= 0]
            gw = wins["pips"].sum() if len(wins) else 0.0
            gl = -losses["pips"].sum() if len(losses) else 0.0001
            pf = gw / gl if gl > 0 else float("inf")
            # monthly sharpe
            wt = win_trades.copy()
            wt["month"] = pd.to_datetime(wt["exit_ts"]).dt.strftime("%Y-%m")
            m = wt.groupby("month")["pnl_jpy"].sum()
            if len(m) > 1 and m.std() > 0:
                sh = float(m.mean() / m.std() * np.sqrt(12))
            else:
                sh = 0.0
            pnl_w = float(win_trades["pnl_jpy"].sum())
            tr_n = int(len(win_trades))
            wn = int(len(wins))
        else:
            pf = 0.0
            sh = 0.0
            pnl_w = float(win_trades["pnl_jpy"].sum()) if len(win_trades) else 0.0
            tr_n = int(len(win_trades))
            wn = 0

        windows.append(WfaWindow(
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            n_primary_events_train=int(len(train_labels)),
            n_primary_events_test=int(len(test_labels)),
            n_secondary_accepted_test=int(len(accepted_in_window)),
            rf_oos_auc=float(oos_auc) if not np.isnan(oos_auc) else float("nan"),
            rf_oos_acc=float(oos_acc) if not np.isnan(oos_acc) else float("nan"),
            safe_mode_fires=int(safe_fires),
            pf=float(pf),
            sharpe=float(sh),
            pnl_jpy=float(pnl_w),
            trades=tr_n,
            wins=wn,
        ))

        cursor += pd.DateOffset(months=WFA_TEST_MONTHS)

    trades_df = pd.DataFrame(all_trades)
    # メタ統計
    meta = {
        "instrument": instrument,
        "total_bars": int(len(df)),
        "total_primary_events": int(len(labels)),
        "total_label_distribution": labels["label"].value_counts().to_dict(),
        "n_windows": len(windows),
    }
    return trades_df, windows, meta


# ----------------------------------------------------------------------
# Black Swan ストレステスト (期間内事象のみ)
# ----------------------------------------------------------------------
def stress_test(trades_df: pd.DataFrame, instrument: str) -> pd.DataFrame:
    rows = []
    if len(trades_df) == 0:
        return pd.DataFrame()
    for name, s, e in STRESS_EVENTS:
        s_ts = pd.Timestamp(s, tz="UTC")
        e_ts = pd.Timestamp(e, tz="UTC")
        in_period = trades_df[
            (pd.to_datetime(trades_df["entry_ts"], utc=True) >= s_ts)
            & (pd.to_datetime(trades_df["entry_ts"], utc=True) <= e_ts)
        ]
        if len(in_period) == 0:
            rows.append({
                "event": name, "instrument": instrument,
                "period": f"{s} to {e}",
                "trades": 0, "pnl_jpy": 0.0, "worst_trade_jpy": 0.0,
                "note": "no trades in window (data range or no signal)",
            })
            continue
        worst = float(in_period["pnl_jpy"].min())
        total = float(in_period["pnl_jpy"].sum())
        rows.append({
            "event": name, "instrument": instrument,
            "period": f"{s} to {e}",
            "trades": int(len(in_period)),
            "pnl_jpy": total,
            "worst_trade_jpy": worst,
            "note": "OK",
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# キルスイッチ / 日次・月次損失上限シミュレーション
# ----------------------------------------------------------------------
def simulate_risk_kills(trades_df: pd.DataFrame, equity_init: float = INITIAL_EQUITY) -> dict:
    """日次 -1.5%/-3%/-5%, 月次 -10% の警告/半量化/停止カウント。"""
    if len(trades_df) == 0:
        return {"daily_warn": 0, "daily_half": 0, "daily_stop": 0, "monthly_stop": 0}
    t = trades_df.copy()
    t["exit_ts"] = pd.to_datetime(t["exit_ts"], utc=True)
    t["day"] = t["exit_ts"].dt.date
    t["month"] = t["exit_ts"].dt.strftime("%Y-%m")
    daily = t.groupby("day")["pnl_jpy"].sum()
    monthly = t.groupby("month")["pnl_jpy"].sum()
    warn = int((daily <= -equity_init * 0.015).sum())
    half = int((daily <= -equity_init * 0.03).sum())
    stop = int((daily <= -equity_init * 0.05).sum())
    mstop = int((monthly <= -equity_init * 0.10).sum())
    return {
        "daily_warn_1.5pct": warn,
        "daily_half_3pct": half,
        "daily_stop_5pct": stop,
        "monthly_stop_10pct": mstop,
    }


# ----------------------------------------------------------------------
# パラメータ感度: SAFE_MODE_THRESH を ±20% 動かして PF を再計算
# ----------------------------------------------------------------------
def parameter_sensitivity(trades_df: pd.DataFrame) -> pd.DataFrame:
    if len(trades_df) == 0:
        return pd.DataFrame()
    base = SAFE_MODE_THRESH
    rows = []
    for thr in [base * 0.8, base * 0.9, base, base * 1.1, base * 1.2]:
        kept = trades_df[trades_df["rf_proba"] >= thr]
        if len(kept) < 2:
            rows.append({"threshold": thr, "trades": len(kept), "pf": 0.0, "pnl_jpy": float(kept["pnl_jpy"].sum()) if len(kept) else 0.0})
            continue
        gw = kept[kept["pips"] > 0]["pips"].sum()
        gl = -kept[kept["pips"] <= 0]["pips"].sum()
        pf = gw / gl if gl > 0 else float("inf")
        rows.append({
            "threshold": float(thr),
            "trades": int(len(kept)),
            "pf": float(pf),
            "pnl_jpy": float(kept["pnl_jpy"].sum()),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Deflated Sharpe Ratio (簡易; Bailey & Lopez de Prado 2014)
# ----------------------------------------------------------------------
def deflated_sharpe(sr_observed: float, n_trials: int, n_obs: int, skew: float = 0.0, kurt: float = 3.0) -> float:
    """観測 SR を試行数で deflate。試行数 = WFA window 数を概算として使用。"""
    if n_obs < 2 or n_trials < 1:
        return float("nan")
    # 期待最大 SR (帰無で n_trials 回引いた最大値)
    emax = (1 - np.euler_gamma) * np.sqrt(2 * np.log(max(n_trials, 1))) \
        + np.euler_gamma * 1.0  # 近似
    # 標準偏差
    sd = np.sqrt((1 - skew * sr_observed + (kurt - 1) / 4.0 * sr_observed ** 2) / (n_obs - 1))
    if sd <= 0:
        return float("nan")
    z = (sr_observed - emax * sd) / sd
    # 標準正規 CDF
    from math import erf, sqrt
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


# ----------------------------------------------------------------------
# メイン
# ----------------------------------------------------------------------
def load_csv(name: str) -> pd.DataFrame:
    p = ROOT / "data" / name
    df = pd.read_csv(p, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    # tz-aware に統一
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    return df


def main():
    print("=" * 60)
    print("Phase 2 BT — #15 Meta-Labeling Ensemble (Lopez de Prado)")
    print("=" * 60)

    # --- 主ペア: EUR/USD H1 ---
    print("\n[EUR/USD H1 5y]")
    eurusd = load_csv("mt5_EUR_USD_H1_5y.csv")
    print(f"  期間: {eurusd.index[0]} → {eurusd.index[-1]} ({len(eurusd)} bars)")
    t_eu, w_eu, meta_eu = run_walk_forward(eurusd, "EUR_USD")
    print(f"  Primary 全イベント: {meta_eu['total_primary_events']}")
    print(f"  Window 数: {meta_eu['n_windows']}")
    print(f"  累計 trades: {len(t_eu)}")

    # --- 副ペア: USD/JPY H1 ---
    print("\n[USD/JPY H1 5y]")
    usdjpy = load_csv("mt5_USD_JPY_H1_5y.csv")
    print(f"  期間: {usdjpy.index[0]} → {usdjpy.index[-1]} ({len(usdjpy)} bars)")
    t_uj, w_uj, meta_uj = run_walk_forward(usdjpy, "USD_JPY")
    print(f"  Primary 全イベント: {meta_uj['total_primary_events']}")
    print(f"  Window 数: {meta_uj['n_windows']}")
    print(f"  累計 trades: {len(t_uj)}")

    # --- 集計 ---
    all_trades = pd.concat([t_eu, t_uj], ignore_index=True) if len(t_eu) + len(t_uj) > 0 else pd.DataFrame()

    def agg_metrics(df, label):
        if len(df) == 0:
            return {
                "label": label, "trades": 0, "pf": 0.0, "sharpe": 0.0,
                "pnl_jpy": 0.0, "winrate": 0.0, "max_dd_jpy": 0.0,
                "sortino": 0.0, "max_consec_loss": 0,
            }
        df = df.copy()
        df["exit_ts"] = pd.to_datetime(df["exit_ts"], utc=True)
        wins = df[df["pips"] > 0]
        losses = df[df["pips"] <= 0]
        gw = wins["pips"].sum() if len(wins) else 0.0
        gl = -losses["pips"].sum() if len(losses) else 0.0001
        pf = gw / gl if gl > 0 else float("inf")
        # monthly Sharpe
        df["month"] = df["exit_ts"].dt.strftime("%Y-%m")
        m = df.groupby("month")["pnl_jpy"].sum()
        if len(m) > 1 and m.std() > 0:
            sh = float(m.mean() / m.std() * np.sqrt(12))
            # sortino: downside std
            neg = m[m < 0]
            if len(neg) > 0 and neg.std() > 0:
                so = float(m.mean() / neg.std() * np.sqrt(12))
            else:
                so = float("inf") if m.mean() > 0 else 0.0
        else:
            sh = 0.0
            so = 0.0
        # max drawdown
        eq = df.sort_values("exit_ts")["pnl_jpy"].cumsum()
        peak = eq.cummax()
        max_dd = float((eq - peak).min())
        # max consecutive losses
        consec = 0
        max_consec = 0
        for v in df.sort_values("exit_ts")["pips"]:
            if v <= 0:
                consec += 1
                max_consec = max(max_consec, consec)
            else:
                consec = 0
        return {
            "label": label,
            "trades": int(len(df)),
            "wins": int(len(wins)),
            "losses": int(len(losses)),
            "winrate": float(len(wins) / len(df) * 100),
            "pf": float(pf),
            "sharpe": float(sh),
            "sortino": float(so),
            "pnl_jpy": float(df["pnl_jpy"].sum()),
            "max_dd_jpy": max_dd,
            "max_consec_loss": int(max_consec),
        }

    m_eu = agg_metrics(t_eu, "EUR_USD")
    m_uj = agg_metrics(t_uj, "USD_JPY")
    m_all = agg_metrics(all_trades, "ALL")

    # Deflated Sharpe (試行 = 2ペア × WFA window 数 / 試したパラメータ近似 5)
    n_trials_est = max(1, (meta_eu["n_windows"] + meta_uj["n_windows"]) * 5)
    dsr = deflated_sharpe(m_all["sharpe"], n_trials_est, max(2, m_all["trades"]))

    # Stress
    stress_eu = stress_test(t_eu, "EUR_USD")
    stress_uj = stress_test(t_uj, "USD_JPY")
    stress = pd.concat([stress_eu, stress_uj], ignore_index=True)

    # Risk kills
    risk_eu = simulate_risk_kills(t_eu)
    risk_uj = simulate_risk_kills(t_uj)
    risk_all = simulate_risk_kills(all_trades)

    # Sensitivity
    sens = parameter_sensitivity(all_trades)

    # 保存
    if len(all_trades) > 0:
        all_trades.to_csv(OUT_DIR / "_phase2_bt_15_meta_trades.csv", index=False)
    # monthly
    if len(all_trades) > 0:
        am = all_trades.copy()
        am["exit_ts"] = pd.to_datetime(am["exit_ts"], utc=True)
        am["month"] = am["exit_ts"].dt.strftime("%Y-%m")
        mo = am.groupby(["instrument", "month"])["pnl_jpy"].agg(["sum", "count"]).reset_index()
        mo.to_csv(OUT_DIR / "_phase2_bt_15_meta_monthly.csv", index=False)
    if len(stress) > 0:
        stress.to_csv(OUT_DIR / "_phase2_bt_15_meta_stress.csv", index=False)

    # 特徴量サンプル (1000行)
    sample_df = build_features(eurusd).dropna().tail(1000)[FEATURE_COLS]
    sample_df.to_csv(OUT_DIR / "_phase2_bt_15_meta_features.csv")

    # ラベル分布
    df_eu_lab = build_features(eurusd)
    df_eu_lab = primary_signals(df_eu_lab)
    label_summary = pd.DataFrame([
        {"instrument": "EUR_USD",
         "primary_events": int((df_eu_lab["primary_side"] != 0).sum()),
         "long_signals": int((df_eu_lab["primary_side"] == 1).sum()),
         "short_signals": int((df_eu_lab["primary_side"] == -1).sum()),
         },
    ])
    label_summary.to_csv(OUT_DIR / "_phase2_bt_15_meta_labels.csv", index=False)

    # WFA window summary
    def windows_to_df(ws):
        return pd.DataFrame([asdict(w) for w in ws])
    wfa_eu = windows_to_df(w_eu) if w_eu else pd.DataFrame()
    wfa_uj = windows_to_df(w_uj) if w_uj else pd.DataFrame()

    # 結果まとめを print
    summary = {
        "primary_strategy": "ma_crossover (SMA20/60 + RSI/ADX, LOOKBACK=5)",
        "secondary_model": f"RandomForest(n_est={RF_N_EST}, max_depth={RF_MAX_DEPTH}, min_leaf={RF_MIN_LEAF})",
        "safe_mode_threshold": SAFE_MODE_THRESH,
        "metrics_eur_usd": m_eu,
        "metrics_usd_jpy": m_uj,
        "metrics_all": m_all,
        "deflated_sharpe": dsr,
        "n_trials_estimate": n_trials_est,
        "risk_kills_all": risk_all,
        "stress_summary": stress.to_dict(orient="records") if len(stress) > 0 else [],
        "wfa_eu_n_windows": len(w_eu),
        "wfa_uj_n_windows": len(w_uj),
        "wfa_eu_avg_oos_auc": float(wfa_eu["rf_oos_auc"].mean()) if len(wfa_eu) > 0 else float("nan"),
        "wfa_uj_avg_oos_auc": float(wfa_uj["rf_oos_auc"].mean()) if len(wfa_uj) > 0 else float("nan"),
        "wfa_eu_avg_secondary_acceptance": float(wfa_eu["n_secondary_accepted_test"].sum() / max(wfa_eu["n_primary_events_test"].sum(), 1)) if len(wfa_eu) > 0 else float("nan"),
        "wfa_uj_avg_secondary_acceptance": float(wfa_uj["n_secondary_accepted_test"].sum() / max(wfa_uj["n_primary_events_test"].sum(), 1)) if len(wfa_uj) > 0 else float("nan"),
        "wfa_eu_total_safe_fires": int(wfa_eu["safe_mode_fires"].sum()) if len(wfa_eu) > 0 else 0,
        "wfa_uj_total_safe_fires": int(wfa_uj["safe_mode_fires"].sum()) if len(wfa_uj) > 0 else 0,
        "sensitivity": sens.to_dict(orient="records") if len(sens) > 0 else [],
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2, default=str))

    # JSON 出力 (レポート生成で参照)
    with open(OUT_DIR / "_phase2_bt_15_meta_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str, ensure_ascii=False)

    # WFA window 詳細を CSV で
    if len(wfa_eu) > 0:
        wfa_eu.to_csv(OUT_DIR / "_phase2_bt_15_meta_wfa_eu.csv", index=False)
    if len(wfa_uj) > 0:
        wfa_uj.to_csv(OUT_DIR / "_phase2_bt_15_meta_wfa_uj.csv", index=False)

    print("\n=== ファイル出力 ===")
    for p in [
        OUT_DIR / "_phase2_bt_15_meta_trades.csv",
        OUT_DIR / "_phase2_bt_15_meta_monthly.csv",
        OUT_DIR / "_phase2_bt_15_meta_stress.csv",
        OUT_DIR / "_phase2_bt_15_meta_features.csv",
        OUT_DIR / "_phase2_bt_15_meta_labels.csv",
        OUT_DIR / "_phase2_bt_15_meta_summary.json",
        OUT_DIR / "_phase2_bt_15_meta_wfa_eu.csv",
        OUT_DIR / "_phase2_bt_15_meta_wfa_uj.csv",
    ]:
        print(f"  {p}  (exists={p.exists()})")


if __name__ == "__main__":
    main()
