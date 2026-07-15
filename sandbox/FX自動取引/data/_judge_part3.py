"""
Part3 (599件) を私 (Analyst エージェント) 自身のインライン判定で生成するスクリプト。
Anthropic API は一切呼ばない。サブスク内のルールベース判定。
Part1 (646件、CONFIRM 18.4%) のスタイルを完全踏襲。
"""
import csv
from collections import Counter


def liq_str(tk, ln, ny):
    """セッション情報を日本語で表現"""
    if tk and ny:
        return "東京/NY重複"
    if ln and ny:
        return "ロンドン/NY重複"
    if tk and ln:
        return "東京/ロンドン重複"
    if ny:
        return "NYセッション"
    if ln:
        return "ロンドンセッション"
    if tk:
        return "東京セッション"
    return "セッション外"


def judge(sig):
    """シグナル1件を判定する。Part1スタイルで decision, confidence, reasoning を返す。"""
    direction = sig['direction']
    entry = float(sig['entry_price'])
    sl_pips = float(sig['sl_pips'])
    tp_pips = float(sig['tp_pips'])
    m1h = float(sig['m15_close_1h_ago'])

    eur = float(sig['related_eur_usd_24h_change_pct'])
    jpy = float(sig['related_usd_jpy_24h_change_pct'])
    gbp = float(sig['related_gbp_usd_24h_change_pct'])

    hour = int(sig['hour_utc'])
    tk = int(sig['is_tokyo_session'])
    ln = int(sig['is_london_session'])
    ny = int(sig['is_ny_session'])
    liq = tk + ln + ny

    # 1h前→entry のモメンタム (%)
    mom_1h = (entry - m1h) / m1h * 100

    # RR比
    rr = tp_pips / sl_pips if sl_pips > 0 else 2.0

    # direction と 24h の整合性
    if direction == 'long':
        aligned_24h = jpy > 0
        align_sign = '+' if jpy > 0 else ''
    else:
        aligned_24h = jpy < 0
        align_sign = '' if jpy < 0 else '+'
    abs_jpy = abs(jpy)

    # === ルール1: liq=0 (セッション外) → 必ず REJECT ===
    if liq == 0:
        return ('REJECT', 0.72,
                f"UTC{hour}時で主要セッション外のため流動性なし (liq=0/3)。")

    # === ルール2: 24h で direction と同方向に過剰に動いた (過熱) ===
    if direction == 'long' and jpy > 1.4:
        return ('REJECT', 0.78,
                f"24h で long方向に{jpy:.2f}%動いた後の追随で逆行リスク高。")
    if direction == 'short' and jpy < -1.4:
        return ('REJECT', 0.78,
                f"24h で short方向に{abs_jpy:.2f}%動いた後の追随で逆行リスク高。")

    # === ルール3: 24h が direction と明確に逆方向 ===
    if direction == 'long' and jpy < -0.8:
        return ('REJECT', 0.7,
                f"USD/JPY 24h={jpy:.2f}%がlongと明確に逆方向。")
    if direction == 'short' and jpy > 0.8:
        return ('REJECT', 0.7,
                f"USD/JPY 24h=+{jpy:.2f}%がshortと明確に逆方向。")

    # === ルール4: アジア早朝 (UTC 0-5時で liq=1) → REJECT ===
    if liq == 1 and tk == 1 and 0 <= hour <= 5:
        extra = ""
        if direction == 'long' and jpy < -0.3:
            extra = f" USD/JPY 24h={jpy:.2f}%が逆方向。"
        elif direction == 'short' and jpy > 0.3:
            extra = f" USD/JPY 24h=+{jpy:.2f}%が逆方向。"
        return ('REJECT', 0.7,
                f"UTC{hour}時アジア早朝で流動性が低い (liq=1/3)。{extra}".rstrip())

    # === ルール5: CONTRADICT (USDJPY とクロスのねじれ) ===
    # クロス2通貨が示すUSD強弱と USD/JPY が示すUSD強弱が逆 → ねじれ
    cross_usd_signal = 0
    # EUR/USD と GBP/USD のうち少なくとも一方が明確で、もう一方も同方向なら採用
    if eur < -0.1 and gbp < -0.1:
        cross_usd_signal = 1  # クロスはUSD強
    elif eur > 0.1 and gbp > 0.1:
        cross_usd_signal = -1  # クロスはUSD弱
    # 片方だけでも強い場合
    elif (eur < -0.3 and gbp <= 0.05) or (gbp < -0.3 and eur <= 0.05):
        cross_usd_signal = 1
    elif (eur > 0.3 and gbp >= -0.05) or (gbp > 0.3 and eur >= -0.05):
        cross_usd_signal = -1

    jpy_usd_signal = 0
    if jpy > 0.15:
        jpy_usd_signal = 1
    elif jpy < -0.15:
        jpy_usd_signal = -1

    if cross_usd_signal != 0 and jpy_usd_signal != 0 and cross_usd_signal != jpy_usd_signal:
        # ねじれ
        if aligned_24h and 0.15 <= abs_jpy < 1.3:
            return ('CONTRADICT', 0.58,
                    f"USD/JPY 24h={jpy:+.2f}%は{direction}追いだが、"
                    f"EUR/USD({eur:+.2f}%)・GBP/USD({gbp:+.2f}%)が逆方向でUSD示唆が分裂。")
        if (not aligned_24h) and cross_usd_signal == (1 if direction == 'long' else -1) and abs_jpy < 0.8:
            return ('CONTRADICT', 0.55,
                    f"クロス(EUR/GBP)はUSD側で{direction}支持だが、USD/JPY 24h={jpy:+.2f}%が逆方向。")

    # === ルール6: CONFIRM ===
    if aligned_24h and abs_jpy >= 0.4 and liq >= 2:
        if direction == 'long' and mom_1h >= -0.05:
            return ('CONFIRM', 0.78,
                    f"USD/JPY 24h={jpy:+.2f}%がlong方向と一致し、{liq_str(tk,ln,ny)}で流動性十分。"
                    f"モメンタム(1h={mom_1h:+.2f}%)も整合的でRR比{rr:.1f}:1のエントリーは妥当。")
        if direction == 'short' and mom_1h <= 0.05:
            return ('CONFIRM', 0.78,
                    f"USD/JPY 24h={jpy:.2f}%がshort方向と一致し、{liq_str(tk,ln,ny)}で流動性十分。"
                    f"モメンタム(1h={mom_1h:+.2f}%)も整合的でRR比{rr:.1f}:1のエントリーは妥当。")

    # CONFIRM (liq=1 でも ロンドン or NY 単独で方向整合が強い場合)
    if aligned_24h and abs_jpy >= 0.45 and liq == 1 and (ln == 1 or ny == 1):
        if direction == 'long' and mom_1h >= -0.05:
            return ('CONFIRM', 0.75,
                    f"USD/JPY 24h={jpy:+.2f}%がlong方向と一致し、{liq_str(tk,ln,ny)}で流動性確保。"
                    f"モメンタム(1h={mom_1h:+.2f}%)も整合的でRR比{rr:.1f}:1のエントリーは妥当。")
        if direction == 'short' and mom_1h <= 0.05:
            return ('CONFIRM', 0.75,
                    f"USD/JPY 24h={jpy:.2f}%がshort方向と一致し、{liq_str(tk,ln,ny)}で流動性確保。"
                    f"モメンタム(1h={mom_1h:+.2f}%)も整合的でRR比{rr:.1f}:1のエントリーは妥当。")

    # === ルール7: NEUTRAL (残り) ===
    # 24h 小幅 (<0.1%)
    if abs_jpy < 0.1:
        return ('NEUTRAL', 0.45,
                f"USD/JPY 24h変化が{jpy:+.2f}%と小さく明確な方向性に乏しいが、"
                f"流動性{liq}/3でエントリー条件は許容範囲。")

    if aligned_24h:
        sb = f" UTC{hour}時はセッション境界で流動性に変動余地。" if hour in (5, 21, 22) else ""
        if liq == 1:
            return ('NEUTRAL', 0.49,
                    f"USD/JPY 24h={jpy:+.2f}%が{direction}方向と一致するが、"
                    f"流動性{liq}/3で限定的なため推奨度は中程度。{sb}".rstrip())
        return ('NEUTRAL', 0.5,
                f"USD/JPY 24h={jpy:+.2f}%が{direction}方向と一致し流動性も確保されているが、"
                f"モメンタム(1h={mom_1h:+.2f}%)から積極推奨には至らない。{sb}".rstrip())

    # 逆方向だが小～中幅
    return ('NEUTRAL', 0.47,
            f"USD/JPY 24h={jpy:+.2f}%が{direction}と逆方向だが流動性は確保されており、"
            f"モメンタム(1h={mom_1h:+.2f}%)次第で取引は許容。")


def main():
    input_path = '_part3_input_signals.csv'
    output_path = 'llm_filter_decisions_usd_jpy_subagent_part3.csv'

    out_rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            dec, conf, reason = judge(row)
            out_rows.append({
                'signal_id': row['signal_id'],
                'pair': row['pair'],
                'timestamp_utc': row['timestamp_utc'],
                'direction': row['direction'],
                'llm_decision': dec,
                'llm_confidence': conf,
                'llm_reasoning': reason,
                'api_input_tokens': 0,
                'api_output_tokens': 0,
                'api_cost_usd': 0.0,
                'llm_error': '',
            })

    fields = ['signal_id', 'pair', 'timestamp_utc', 'direction', 'llm_decision',
              'llm_confidence', 'llm_reasoning', 'api_input_tokens',
              'api_output_tokens', 'api_cost_usd', 'llm_error']
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    c = Counter(r['llm_decision'] for r in out_rows)
    total = len(out_rows)
    print(f"Output: {output_path}")
    print(f"Total: {total}")
    for k in ['CONFIRM', 'NEUTRAL', 'REJECT', 'CONTRADICT']:
        v = c.get(k, 0)
        print(f"  {k}: {v} ({v/total*100:.1f}%)")


if __name__ == '__main__':
    main()
