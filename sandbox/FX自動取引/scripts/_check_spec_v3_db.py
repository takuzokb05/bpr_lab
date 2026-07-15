# SPEC v3 デモDBの取引状況スナップショット取得（VPS上で実行）
import sqlite3
import json

DB = r"C:\bpr_lab_spec_v2\sandbox\FX自動取引\data\fx_spec_v3.db"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

out = {}
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
out["tables"] = tables

for t in tables:
    out[f"count_{t}"] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

# 取引テーブルらしきものを探して中身を出す
for t in tables:
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})")]
    out[f"cols_{t}"] = cols

print(json.dumps(out, ensure_ascii=False, default=str))
