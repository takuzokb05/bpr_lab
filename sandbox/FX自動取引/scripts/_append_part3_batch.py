# 役割: Analyst が判定済みの CSV 行を Part3 に追記するだけの I/O スクリプト
# 判定ロジックは含まない (= Python 関数で判定していない)
import sys
import io

# UTF-8 で標準出力をラップ
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT_PATH = r"C:/Users/takuz/プロジェクト/bpr_lab/sandbox/FX自動取引/data/llm_filter_decisions_usd_jpy_context_part3.csv"

# 追記する行は引数ファイルから読む (Analyst が事前に書いた事実)
input_rows_path = sys.argv[1]
with open(input_rows_path, "r", encoding="utf-8") as f:
    rows = f.read()

with open(OUT_PATH, "a", encoding="utf-8", newline="") as f:
    if not rows.endswith("\n"):
        rows = rows + "\n"
    f.write(rows)

print(f"appended bytes: {len(rows.encode('utf-8'))}")
