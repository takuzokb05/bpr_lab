# SPEC v3 デモの取引明細・PF・撤退発火状況の詳細取得（VPS上で実行）
import sqlite3
import json

DB = r"C:\bpr_lab_spec_v2\sandbox\FX自動取引\data\fx_spec_v3.db"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

out = {}

out["trades"] = [dict(r) for r in cur.execute(
    "SELECT t.id, t.mt5_ticket, t.entry_at_utc, t.pair, t.direction, t.lots, "
    "t.entry_price, t.sl_pips, t.tp_pips, t.llm_label, t.llm_confidence, t.status, "
    "c.exit_at_utc, c.exit_reason, c.pnl_pips, c.pnl_jpy, c.holding_minutes "
    "FROM trades t LEFT JOIN trade_closures c ON c.trade_id = t.id ORDER BY t.id")]

out["judgment_summary"] = [dict(r) for r in cur.execute(
    "SELECT pair, llm_label, accepted, COUNT(*) AS n, AVG(llm_confidence) AS avg_conf, "
    "SUM(api_cost_usd) AS cost FROM llm_judgments GROUP BY pair, llm_label, accepted")]

out["api_errors"] = [dict(r) for r in cur.execute(
    "SELECT judged_at_utc, pair, api_error FROM llm_judgments "
    "WHERE api_error IS NOT NULL AND api_error != '' ORDER BY id DESC LIMIT 10")]

out["loop_health_recent"] = [dict(r) for r in cur.execute(
    "SELECT event_at_utc, event_type, pair, message FROM loop_health ORDER BY id DESC LIMIT 20")]

out["total_cost_usd"] = cur.execute("SELECT SUM(api_cost_usd) FROM llm_judgments").fetchone()[0]

print(json.dumps(out, ensure_ascii=False, default=str))
