"""USD_JPYの全取引と経済指標発表時刻の突合"""
import sqlite3
import sys
from datetime import datetime, timezone, timedelta

db_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\bpr_lab\sandbox\FX自動取引\data\fx_trading.db'
c = sqlite3.connect(db_path)
cur = c.cursor()

print('=== USD_JPY 全取引（開閉時刻、PL）===')
cur.execute("""
    SELECT id, trade_id, units, open_price, close_price, stop_loss, take_profit,
           pl, opened_at, closed_at, status
    FROM trades
    WHERE instrument = 'USD_JPY'
    ORDER BY opened_at ASC
""")
trades = cur.fetchall()
for r in trades:
    print(r)

print()
print('=== 各取引の保有時間と勝敗 ===')
print(f"{'id':<4}{'trade_id':<12}{'side':<6}{'open(UTC)':<22}{'close(UTC)':<22}{'duration':<14}{'pl':<8}")
for r in trades:
    id_, trade_id, units, op, cp, sl, tp, pl, oa, ca, st = r
    side = 'BUY' if units > 0 else 'SELL'
    if ca:
        try:
            ot = datetime.fromisoformat(oa.replace('Z', '+00:00'))
            ct = datetime.fromisoformat(ca.replace('+00:00', '+00:00') if '+' in ca else ca + '+00:00')
            dur = ct - ot
            dur_str = f"{int(dur.total_seconds()//3600)}h{int((dur.total_seconds()%3600)//60)}m"
        except Exception as e:
            dur_str = f"err:{e}"
            ot = oa
            ct = ca
        print(f"{id_:<4}{trade_id:<12}{side:<6}{str(ot):<22}{str(ct):<22}{dur_str:<14}{pl}")
    else:
        print(f"{id_:<4}{trade_id:<12}{side:<6}{oa:<22}{'OPEN':<22}{'-':<14}-")

# 経済指標カレンダー（2026/04 - 2026/05、UTC）
# 出典: 一般的な公表時刻 + risk_factors記載内容から逆算
# NFP: First Friday of month, 12:30 UTC (公開時刻が13:30JSTサマータイム後8:30EST→12:30UTC)
# FOMC: 18:00-18:30 UTC (FOMC声明), 18:30-19:00 UTC (会見)
# BoJ: 03:00-04:00 UTC (政策決定発表), 06:30 UTC会見
# ISM: 14:00 UTC (10:00 EST)
# JOLTS: 14:00 UTC (10:00 EST)
# ADP: 12:15 UTC (8:15 EST)
events_2026 = [
    # NFP (毎月第1金曜)
    ('2026-04-03 12:30', 'NFP 4月分'),
    ('2026-05-01 12:30', 'NFP 5月分'),  # 但しGW中
    # 最新の market_analysis.json risk_factors に「米雇用統計（NFP）...今週」とあるので 5/2 (金) 12:30 UTC が今週分
    ('2026-05-02 12:30', 'NFP 5月分（実）'),
    # FOMC（risk_factorsに「FOMC内部の意見対立」とある = 直近のFOMCあった）
    ('2026-04-29 18:00', 'FOMC声明'),
    ('2026-04-29 18:30', 'FOMC会見'),
    # BoJ（risk_factorsに「日銀による5兆円規模の為替介入観測」「日銀の追加為替介入リスク」とある）
    ('2026-04-30 03:00', 'BoJ政策決定'),  # 通常会合
    ('2026-04-30 06:30', 'BoJ植田会見'),
    # ISM/ADP/JOLTS（risk_factors記載）
    ('2026-05-01 14:00', 'ISM製造業'),
    ('2026-05-02 12:15', 'ADP雇用'),
    ('2026-05-02 14:00', 'ISM非製造業'),
    ('2026-04-30 14:00', 'JOLTS求人'),
]
print()
print('=== 経済指標カレンダー（推定）===')
for et, name in events_2026:
    print(f"  {et} UTC  {name}")

print()
print('=== USD_JPY 取引と経済指標の時間距離 ===')
print(f"{'id':<4}{'open(UTC)':<22}{'pl':<8}{'近接イベント':<60}")
for r in trades:
    id_, trade_id, units, op, cp, sl, tp, pl, oa, ca, st = r
    try:
        ot = datetime.fromisoformat(oa.replace('Z', '+00:00'))
    except Exception:
        continue
    # 各イベントとの時間差
    nearest = []
    for et, name in events_2026:
        ev = datetime.strptime(et, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
        diff_open = (ev - ot).total_seconds() / 3600  # hours
        # 開始or決済から±24hの範囲のイベントを抽出
        if abs(diff_open) <= 24:
            sign = '前' if diff_open > 0 else '後'
            nearest.append(f"{name} {abs(diff_open):.1f}h{sign}")
        if ca:
            try:
                ct = datetime.fromisoformat(ca.replace('+00:00', '+00:00') if '+' in ca else ca + '+00:00')
                diff_close = (ev - ct).total_seconds() / 3600
                if abs(diff_close) <= 6 and abs(diff_close) < abs(diff_open):
                    # 決済時刻のすぐ周辺
                    nearest.append(f"[決済≈]{name} {abs(diff_close):.1f}h")
            except Exception:
                pass
    pl_str = f"{pl:+.0f}" if pl is not None else "OPEN"
    print(f"{id_:<4}{str(ot)[:19]:<22}{pl_str:<8}{', '.join(nearest[:3]) if nearest else '(イベント±24h圏外)':<60}")

print()
print('=== サマリ：勝敗別の経済指標近接率 ===')
win_close_to_event = 0
loss_close_to_event = 0
win_total = 0
loss_total = 0
for r in trades:
    id_, trade_id, units, op, cp, sl, tp, pl, oa, ca, st = r
    if pl is None:
        continue
    try:
        ot = datetime.fromisoformat(oa.replace('Z', '+00:00'))
        ct = datetime.fromisoformat(ca.replace('+00:00', '+00:00') if '+' in ca else ca + '+00:00')
    except Exception:
        continue
    in_event_window = False
    for et, name in events_2026:
        ev = datetime.strptime(et, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
        # イベントが open〜close の保有期間内に入っているか、もしくは±2h圏か
        if (ot - timedelta(hours=2)) <= ev <= (ct + timedelta(hours=2)):
            in_event_window = True
            break
    if pl > 0:
        win_total += 1
        if in_event_window:
            win_close_to_event += 1
    else:
        loss_total += 1
        if in_event_window:
            loss_close_to_event += 1

print(f"勝ち: {win_total}件, うち重要指標近接(±2h以内 or 保有期間中): {win_close_to_event}件 ({100*win_close_to_event/max(win_total,1):.0f}%)")
print(f"負け: {loss_total}件, うち重要指標近接(±2h以内 or 保有期間中): {loss_close_to_event}件 ({100*loss_close_to_event/max(loss_total,1):.0f}%)")
