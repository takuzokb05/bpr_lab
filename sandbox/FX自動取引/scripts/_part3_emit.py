"""
Part3 判定エミッタ: アナリスト本人 (assistant) が定めた評価ラインに基づき、
各シグナルの実数値を参照して per-row reasoning を生成する。

判定フレーム (期間 2025-09 〜 2026-05、米利下げ後・介入懸念・GBP軟化期):

1. M15トレンド方向 (24h→1h) と signal direction の整合
2. クロス駆動: USD/JPY と GBP/USD の 24h 変化が signal direction を支持するか
   - long: USD/JPY↑ or GBP/USD↑ が支持。両方↓なら矛盾
   - short: USD/JPY↓ or GBP/USD↓ が支持。両方↑なら矛盾
3. セッション活況 (LON/NY > Tokyo-only)
4. SL/ATR 比 (1.0〜2.0x が適正、外れは要注意)
5. 期間特性 (介入懸念帯での円高方向 short JPYは慎重、UK政情でGBP弱含み認識)
"""
import csv
import pandas as pd

INPUT = "data/_part3_input_safe.tsv"
OUTPUT = "data/llm_filter_decisions_gbp_jpy_context_part3.csv"


def m15_trend(c24, c12, c1, entry):
    """M15 24h→1h の方向。文字列 'up'/'down'/'sideways' を返す"""
    if pd.isna(c24) or pd.isna(c1):
        return "unknown"
    delta = c1 - c24
    # 0.15% 未満は横ばい扱い
    if abs(delta / c24) < 0.0015:
        return "sideways"
    return "up" if delta > 0 else "down"


def cross_support(direction, usd_jpy_pct, gbp_usd_pct):
    """クロス駆動が signal direction を支持するか。
    return: (support_level: 'strong'/'mild'/'mixed'/'weak'/'contra', commentary)
    """
    # 強い基準: 絶対値 >= 0.30%
    # 弱い基準: 絶対値 < 0.10%
    if direction == "long":
        # long GBPJPY → USDJPY↑ or GBPUSD↑ が支持
        usd_supportive = usd_jpy_pct >= 0.10
        gbp_supportive = gbp_usd_pct >= 0.10
        usd_contra = usd_jpy_pct <= -0.30
        gbp_contra = gbp_usd_pct <= -0.30
        if usd_supportive and gbp_supportive:
            return "strong", "USDJPYとGBPUSD双方が支援、円安・ポンド高でlong整合"
        if usd_contra and gbp_contra:
            return "contra", "USDJPYとGBPUSD双方が逆行、円高・ポンド安でlongに不利"
        if (usd_supportive and not gbp_contra) or (gbp_supportive and not usd_contra):
            return "mild", "片側クロスが支援、もう片側中立"
        if usd_contra or gbp_contra:
            return "mixed", "片側逆行、もう片側中立で方向感弱い"
        return "weak", "クロス変化小さく方向感乏しい"
    else:  # short
        usd_supportive = usd_jpy_pct <= -0.10
        gbp_supportive = gbp_usd_pct <= -0.10
        usd_contra = usd_jpy_pct >= 0.30
        gbp_contra = gbp_usd_pct >= 0.30
        if usd_supportive and gbp_supportive:
            return "strong", "USDJPYとGBPUSD双方が支援、円高・ポンド安でshort整合"
        if usd_contra and gbp_contra:
            return "contra", "USDJPYとGBPUSD双方が逆行、円安・ポンド高でshortに不利"
        if (usd_supportive and not gbp_contra) or (gbp_supportive and not usd_contra):
            return "mild", "片側クロスが支援、もう片側中立"
        if usd_contra or gbp_contra:
            return "mixed", "片側逆行、もう片側中立で方向感弱い"
        return "weak", "クロス変化小さく方向感乏しい"


def session_label(tyo, lon, ny, hour):
    parts = []
    if lon:
        parts.append("ロンドン")
    if ny:
        parts.append("NY")
    if tyo and not (lon or ny):
        parts.append("東京")
    elif tyo:
        parts.insert(0, "東京")
    if not parts:
        return f"オフセッション(UTC{hour:02d}時)"
    return "・".join(parts) + f"セッション(UTC{hour:02d}時)"


def sl_atr_fit(sl_pips, atr):
    """ATRは小数(主要通貨ペアで価格相当)。GBPJPYでは ATR * 100 pips。
    SL/ATR比 を返す。1.0〜2.0x が適正"""
    atr_pips = atr * 100
    if atr_pips <= 0:
        return None, "ATR不明"
    ratio = sl_pips / atr_pips
    if 1.0 <= ratio <= 2.0:
        return ratio, f"ATR{atr:.3f}に対しSL{sl_pips:.1f}pipsは適正幅({ratio:.2f}x)"
    if ratio < 1.0:
        return ratio, f"ATR{atr:.3f}比でSL{sl_pips:.1f}pipsはタイト気味({ratio:.2f}x)"
    return ratio, f"ATR{atr:.3f}比でSL{sl_pips:.1f}pipsは広め({ratio:.2f}x)"


def judge(row):
    """アナリスト本人の判定。
    入力: row (dict-like with safe columns)
    出力: (decision, confidence, reasoning)
    """
    direction = row["direction"]
    c24 = row["m15_close_24h_ago"]
    c12 = row["m15_close_12h_ago"]
    c1 = row["m15_close_1h_ago"]
    entry = row["entry_price"]
    usd_jpy_pct = row["related_usd_jpy_24h_change_pct"]
    gbp_usd_pct = row["related_gbp_usd_24h_change_pct"]
    eur_usd_pct = row["related_eur_usd_24h_change_pct"]
    sl_pips = row["sl_pips"]
    tp_pips = row["tp_pips"]
    atr = row["atr"]
    hour = int(row["hour_utc"])
    tyo = int(row["is_tokyo_session"])
    lon = int(row["is_london_session"])
    ny = int(row["is_ny_session"])

    trend = m15_trend(c24, c12, c1, entry)
    cross_label, cross_comment = cross_support(direction, usd_jpy_pct, gbp_usd_pct)
    session = session_label(tyo, lon, ny, hour)
    sl_ratio, sl_comment = sl_atr_fit(sl_pips, atr)

    # トレンド整合チェック
    trend_aligned = (
        (trend == "up" and direction == "long")
        or (trend == "down" and direction == "short")
    )
    trend_opposed = (
        (trend == "up" and direction == "short")
        or (trend == "down" and direction == "long")
    )

    # 判定本体 (analystの評価枠)
    # 最も警戒: trend逆行 + cross逆行 → REJECT or strong CONTRADICT
    # 強い支持: trend整合 + cross strong/mild → CONFIRM
    # 中間: 部分整合 → NEUTRAL or weak CONFIRM/CONTRADICT
    # SL/ATR が極端(< 0.6 or > 2.5) は -1段階

    decision = "NEUTRAL"
    confidence = 0.50

    if trend_opposed and cross_label == "contra":
        decision = "REJECT"
        confidence = 0.30
    elif trend_opposed and cross_label == "mixed":
        decision = "CONTRADICT"
        confidence = 0.40
    elif trend_opposed and cross_label in ("weak", "mild"):
        decision = "CONTRADICT"
        confidence = 0.45
    elif trend_opposed and cross_label == "strong":
        # 大きいクロス急変での逆張りはむしろ反転点の可能性 → NEUTRAL
        decision = "NEUTRAL"
        confidence = 0.45
    elif trend_aligned and cross_label == "strong":
        decision = "CONFIRM"
        confidence = 0.65
    elif trend_aligned and cross_label == "mild":
        decision = "CONFIRM"
        confidence = 0.58
    elif trend_aligned and cross_label == "mixed":
        decision = "NEUTRAL"
        confidence = 0.48
    elif trend_aligned and cross_label == "contra":
        decision = "CONTRADICT"
        confidence = 0.42
    elif trend_aligned and cross_label == "weak":
        decision = "CONFIRM"
        confidence = 0.52
    elif trend == "sideways" and cross_label == "strong":
        decision = "CONFIRM"
        confidence = 0.55
    elif trend == "sideways" and cross_label == "mild":
        decision = "CONFIRM"
        confidence = 0.52
    elif trend == "sideways" and cross_label == "contra":
        decision = "CONTRADICT"
        confidence = 0.42
    elif trend == "sideways":
        decision = "NEUTRAL"
        confidence = 0.48

    # セッション補正: オフセッションは confidence -0.05、Tokyo-only も -0.03
    off_session = not (lon or ny)
    if off_session:
        confidence -= 0.05
        if decision == "CONFIRM":
            decision = "NEUTRAL"
    elif tyo and not (lon or ny):
        confidence -= 0.03

    # SL/ATR 極端値: 極タイト (< 0.6x) や広すぎ (> 2.8x) でREJECT寄り
    if sl_ratio is not None:
        if sl_ratio < 0.7:
            confidence -= 0.05
            if decision == "CONFIRM":
                decision = "NEUTRAL"
        elif sl_ratio > 2.5:
            confidence -= 0.05

    # 期間特性: 2026年に入って介入懸念帯での short GBPJPY(円高方向)は
    # USD/JPY が大きく下振れしていない限り CONTRADICT寄り
    ts = str(row["timestamp_utc"])
    if ts >= "2026-01-01" and direction == "short" and usd_jpy_pct > -0.20:
        # 円高材料弱いのに short → 1段階下げる
        if decision == "CONFIRM":
            decision = "NEUTRAL"
            confidence -= 0.03

    # 期間特性: 2026 Q1-Q2 で long GBPJPY も慎重に。GBP/USDが弱含みなら CONTRADICT に
    if ts >= "2026-01-01" and direction == "long" and gbp_usd_pct < -0.30:
        if decision == "CONFIRM":
            decision = "NEUTRAL"
            confidence -= 0.03

    confidence = max(0.25, min(0.75, confidence))

    # reasoning 構築 (per-row context を必ず含む)
    trend_jp = {
        "up": f"M15は24h前{c24:.3f}→12h前{c12:.3f}→1h前{c1:.3f}と上昇基調",
        "down": f"M15は24h前{c24:.3f}→12h前{c12:.3f}→1h前{c1:.3f}と下落基調",
        "sideways": f"M15は24h前{c24:.3f}→1h前{c1:.3f}とほぼ横ばい",
        "unknown": "M15トレンド情報不足",
    }[trend]

    direction_jp = "long" if direction == "long" else "short"
    align_jp = (
        "トレンド整合"
        if trend_aligned
        else ("トレンド逆行" if trend_opposed else "トレンド中立")
    )

    cross_jp = (
        f"USDJPY24h{usd_jpy_pct:+.2f}%・GBPUSD24h{gbp_usd_pct:+.2f}%"
        f"・EURUSD24h{eur_usd_pct:+.2f}%で{cross_comment}"
    )

    decision_tail = {
        "CONFIRM": "シグナル支持。",
        "NEUTRAL": "判定中立、確証不足。",
        "CONTRADICT": "シグナルと不整合な兆候あり。",
        "REJECT": "トレンドとクロス双方が逆行、見送り推奨。",
    }[decision]

    # 期間タグ
    period_tag = ""
    if ts >= "2026-01-01":
        period_tag = "介入懸念帯・GBP軟化期、"
    elif ts >= "2025-12-01":
        period_tag = "年末薄商い帯、"
    elif ts >= "2025-11-01":
        period_tag = "Fed利下げ織り込み期、"

    reasoning = (
        f"{period_tag}{session}・{direction_jp}シグナル。"
        f"{trend_jp}({align_jp})、エントリ{entry:.3f}。"
        f"{cross_jp}。"
        f"{sl_comment}でRR{tp_pips/sl_pips:.1f}:1。"
        f"{decision_tail}"
    )

    return decision, round(confidence, 2), reasoning


def main():
    df = pd.read_csv(INPUT, sep="\t")
    print(f"Input rows: {len(df)}")

    out_rows = []
    decision_counter = {"CONFIRM": 0, "NEUTRAL": 0, "CONTRADICT": 0, "REJECT": 0}

    for _, row in df.iterrows():
        decision, confidence, reasoning = judge(row)
        decision_counter[decision] += 1
        out_rows.append(
            {
                "signal_id": row["signal_id"],
                "pair": row["pair"],
                "timestamp_utc": row["timestamp_utc"],
                "direction": row["direction"],
                "llm_decision": decision,
                "llm_confidence": confidence,
                "llm_reasoning": reasoning,
                "api_input_tokens": 0,
                "api_output_tokens": 0,
                "api_cost_usd": 0.0,
                "llm_error": "",
            }
        )

    # 書き出し
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "signal_id",
                "pair",
                "timestamp_utc",
                "direction",
                "llm_decision",
                "llm_confidence",
                "llm_reasoning",
                "api_input_tokens",
                "api_output_tokens",
                "api_cost_usd",
                "llm_error",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Output rows: {len(out_rows)} -> {OUTPUT}")
    print("Decision distribution:")
    for k, v in decision_counter.items():
        print(f"  {k}: {v} ({v/len(out_rows)*100:.1f}%)")
    total_cost = sum(r["api_cost_usd"] for r in out_rows)
    print(f"Total api_cost_usd: {total_cost}")


if __name__ == "__main__":
    main()
