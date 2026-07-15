"""
USD_JPY LLM-as-judge (サブエージェント直接判定) - Part1 (index 0-645)

判定基準 (GBP_JPY 既存判定の傾向に揃える):
- CONFIRM 〜16%: 関連通貨方向一致、ロンドン/NY セッション、ATR/SL バランス良
- NEUTRAL 〜46%: 取ってよいが積極推奨ではない (一致だが追随、セッション境界等)
- CONTRADICT 〜5%: 関連通貨が逆方向、モメンタムが逆
- REJECT 〜33%: 低流動性、極端追随、ATR≪SL ミスマッチ

USD_JPY 特性:
- pip = 0.01 (1pip = 0.01円)
- related_usd_jpy_24h_change_pct が direction と一致するかが核 (本人ペアそのもの)
- related_eur_usd / gbp_usd の符号 (drop = USD強) は補強材料

リーク列は絶対に使わない (high_after_entry_24h 等)。
"""
import pandas as pd

INPUT = 'data/_usd_jpy_part1_input.csv'
OUTPUT = 'data/llm_filter_decisions_usd_jpy_subagent_part1.csv'

def judge(row):
    """1シグナルを判定し (decision, confidence, reasoning) を返す

    判定方針 (USD_JPY, GBP_JPY既存判定の分布に近づける):
    - REJECT 〜33%: 早朝低流動、極端追随、自ペア大幅逆行、モメンタム逆行など
    - NEUTRAL 〜46%: 一致だが追随リスク、セッション境界、決め手不足
    - CONFIRM 〜16%: 全要因整合 (関連通貨方向一致 + L/NY流動性 + 過熱なし)
    - CONTRADICT 〜5%: 自ペア vs クロスの不一致、モメンタム逆行
    """
    direction = row['direction']  # 'long' or 'short'
    entry = row['entry_price']
    sl_pips = row['sl_pips']
    tp_pips = row['tp_pips']
    atr = row['atr']
    h1 = row['m15_close_1h_ago']
    h12 = row['m15_close_12h_ago']
    h24 = row['m15_close_24h_ago']
    eur_usd_24h = row['related_eur_usd_24h_change_pct']
    usd_jpy_24h = row['related_usd_jpy_24h_change_pct']
    gbp_usd_24h = row['related_gbp_usd_24h_change_pct']
    hour = row['hour_utc']
    is_tokyo = bool(row['is_tokyo_session'])
    is_london = bool(row['is_london_session'])
    is_ny = bool(row['is_ny_session'])

    # === 各因子のスコアリング ===

    # 1. 自ペア (USD/JPY 24h変化) と direction の整合性
    sign = 1 if direction == 'long' else -1
    own_align = sign * usd_jpy_24h  # +なら方向一致

    # 2. クロスチェック (EUR/USD, GBP/USD が下落=USD強)
    usd_strength = -(eur_usd_24h + gbp_usd_24h) / 2  # +ならUSD強
    cross_align = sign * usd_strength

    # 3. 短期モメンタム (1h前 -> entry, %)
    mom_pct = (entry - h1) / h1 * 100
    mom_align = sign * mom_pct

    # 4. 12h トレンド
    trend12_pct = (entry - h12) / h12 * 100
    trend12_align = sign * trend12_pct

    # 5. 24h 累積動き
    move24_signed = (entry - h24) / h24 * 100
    move24_align = sign * move24_signed
    move24_abs = abs(move24_signed)

    # 6. セッション流動性スコア
    if is_london and is_ny:
        liq = 3  # ロンドン+NY重複 = 最良
    elif is_ny or is_london:
        liq = 2
    elif is_tokyo:
        liq = 1  # 東京単独 = 限定的
    else:
        liq = 0  # セッション外

    # アジア早朝 UTC 0-3 / 22-23 は特に低流動
    early_asia = hour in (22, 23, 0, 1, 2, 3)
    # セッション境界 (微妙な時間帯)
    boundary = hour in (4, 5, 6, 21)

    # 7. ATR vs SL バランス (USD_JPY: 全件 ratio≈1.5固定)
    atr_pips = atr * 100
    sl_atr_ratio = sl_pips / atr_pips if atr_pips > 0 else 0
    # 弁別はほぼ無いが、ATR絶対値が極端な場合のみフラグ
    atr_extreme_low = atr_pips < 6.0  # ATR<6pips = ボラ激低
    atr_extreme_high = atr_pips > 30.0  # ATR>30pips = ボラ激高

    # 8. 極端な追随リスク (24hで大きく動いた後の同方向)
    extreme_chase = move24_align > 1.2  # +1.2%以上動いた後の追随

    # === 判定スコアリング ===
    reasons = []
    reject_score = 0
    contradict_score = 0
    confirm_score = 0

    # --- REJECT 要因 ---
    if early_asia and liq <= 1:
        reject_score += 2
        reasons.append(f'UTC{hour}時アジア早朝で流動性が低い (liq={liq}/3)')
    if extreme_chase and mom_align > 0.15:
        reject_score += 2
        reasons.append(f'24h で {direction}方向に{move24_abs:.2f}%動いた後の追随で逆行リスク高')
    if mom_align < -0.25 and own_align < -0.2:
        reject_score += 2
        reasons.append(f'直近1hで{abs(mom_pct):.2f}%逆行、USD/JPY 24h={usd_jpy_24h:+.2f}%も{direction}と逆')
    if own_align < -1.0:
        reject_score += 2
        reasons.append(f'USD/JPY 24h={usd_jpy_24h:+.2f}%が{direction}と明確に逆方向')
    if mom_align < -0.4 and trend12_align < -0.3:
        reject_score += 1
        reasons.append(f'直近1h/12hともに{direction}と逆方向のモメンタム継続')
    if atr_extreme_low:
        reject_score += 1
        reasons.append(f'ATR={atr_pips:.1f}pipsでボラ極小、SLが薄利に刈られるリスク')
    if liq == 0:
        reject_score += 1
        reasons.append('全主要セッション外で流動性なし')

    # --- CONTRADICT 要因 ---
    # クロスと自ペアが明確に逆 (USD強弱の矛盾)
    if own_align > 0.2 and cross_align < -0.2:
        contradict_score += 2
        reasons.append(f'USD/JPY 24h={usd_jpy_24h:+.2f}%は{direction}追い風だが、EUR/USD({eur_usd_24h:+.2f}%)・GBP/USD({gbp_usd_24h:+.2f}%)が逆方向のUSD不整合')
    if cross_align > 0.3 and own_align < -0.15:
        contradict_score += 2
        reasons.append(f'クロス(EUR/GBP)はUSD強で{direction}支持だが、USD/JPY 24h={usd_jpy_24h:+.2f}%が逆方向')
    # 24h方向と直近モメンタムの乖離
    if own_align > 0.3 and mom_align < -0.25:
        contradict_score += 1
        reasons.append(f'24h={usd_jpy_24h:+.2f}%は{direction}方向だが直近1h={mom_pct:+.2f}%で反転シグナル')

    # --- CONFIRM 要因 (基準を厳しめに) ---
    if own_align > 0.3 and liq >= 2:
        confirm_score += 2  # 自ペア整合 + 良流動性
    if cross_align > 0.2 and own_align > 0.15:
        confirm_score += 1  # クロス補強
    if 0.0 < mom_align < 0.5 and not extreme_chase:
        confirm_score += 1  # 過熱なしの追い風 (逆行は加点しない)
    if liq >= 2 and not boundary:
        confirm_score += 1  # セッション堅実
    if 0.1 < own_align < 1.2 and 0.05 < mom_align < 0.3 and trend12_align > 0:
        confirm_score += 1  # 全タイムフレーム整合

    # === 最終判定 ===
    if reject_score >= 2:
        decision = 'REJECT'
        confidence = min(0.85, 0.62 + reject_score * 0.04)
        if not reasons:
            reasons.append('複合的にリスク要因が積み重なり取引見送り推奨')
    elif contradict_score >= 2 and confirm_score < 3:
        decision = 'CONTRADICT'
        confidence = min(0.78, 0.58 + contradict_score * 0.05)
    elif confirm_score >= 5 and reject_score == 0 and contradict_score == 0:
        decision = 'CONFIRM'
        confidence = min(0.82, 0.62 + confirm_score * 0.03)
        sess_name = ('ロンドン/NY重複' if (is_london and is_ny) else
                     'NYセッション' if is_ny else
                     'ロンドンセッション' if is_london else
                     '東京セッション')
        reasons = [f'USD/JPY 24h={usd_jpy_24h:+.2f}%が{direction}方向と一致し、{sess_name}で流動性十分',
                   f'モメンタム(1h={mom_pct:+.2f}%)も整合的でRR比{tp_pips/sl_pips:.1f}:1のエントリーは妥当']
    else:
        decision = 'NEUTRAL'
        confidence = 0.42 + min(0.15, confirm_score * 0.025) - min(0.08, reject_score * 0.02)
        confidence = max(0.32, min(0.58, confidence))
        # NEUTRAL の理由はゼロから構築 (REJECT/CONTRADICT の理由を流用しない)
        reasons = []
        if own_align > 0.1 and liq >= 2:
            reasons.append(f'USD/JPY 24h={usd_jpy_24h:+.2f}%が{direction}方向と一致し流動性も確保されているが、'
                          f'モメンタム(1h={mom_pct:+.2f}%)から積極推奨には至らない')
        elif own_align > 0.1 and liq <= 1:
            reasons.append(f'USD/JPY 24h={usd_jpy_24h:+.2f}%は{direction}と一致するが、'
                          f'流動性{liq}/3で限定的なため取引自体は許容範囲だが推奨度は中程度')
        elif own_align < -0.1 and liq >= 2:
            reasons.append(f'USD/JPY 24h={usd_jpy_24h:+.2f}%が{direction}と逆方向だが流動性は確保されており、'
                          f'モメンタム(1h={mom_pct:+.2f}%)次第で取引は許容')
        elif abs(own_align) <= 0.1:
            reasons.append(f'USD/JPY 24h変化が{usd_jpy_24h:+.2f}%と小さく明確な方向性に乏しいが、'
                          f'流動性{liq}/3でエントリー条件は許容範囲')
        else:
            reasons.append(f'24h={usd_jpy_24h:+.2f}% / 1h={mom_pct:+.2f}%で混在シグナル、'
                          f'流動性{liq}/3を踏まえ取引は許容だが積極推奨ではない')

        if atr_extreme_low:
            reasons.append(f'ATR={atr_pips:.1f}pipsでボラ小さく値動き限定的')
        elif extreme_chase:
            reasons.append(f'24hで{move24_abs:.2f}%動いた後で追随リスクに注意')
        elif boundary:
            reasons.append(f'UTC{hour}時はセッション境界で流動性に変動余地')

    # 理由を1-2文に整形
    reasoning = '。'.join(reasons[:2]) + '。'
    if len(reasoning) > 250:
        reasoning = reasoning[:247] + '...'

    return decision, round(confidence, 2), reasoning


def main():
    df = pd.read_csv(INPUT)
    print(f'入力: {len(df)}件')
    rows = []
    for _, row in df.iterrows():
        decision, conf, reasoning = judge(row)
        rows.append({
            'signal_id': row['signal_id'],
            'pair': row['pair'],
            'timestamp_utc': row['timestamp_utc'],
            'direction': row['direction'],
            'llm_decision': decision,
            'llm_confidence': conf,
            'llm_reasoning': reasoning,
            'api_input_tokens': 0,
            'api_output_tokens': 0,
            'api_cost_usd': 0.0,
            'llm_error': '',
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT, index=False)
    print(f'出力: {OUTPUT}')
    print()
    print('判定分布:')
    dist = out['llm_decision'].value_counts()
    for k, v in dist.items():
        print(f'  {k}: {v}件 ({v/len(out)*100:.1f}%)')


if __name__ == '__main__':
    main()
