"""
中断された LLM Filter の CSV から、API クレジット切れエラー行を除外して
clean 版 CSV を生成する。
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

for pair, path in [
    ("USD_JPY", ROOT / "data" / "llm_filter_decisions_usd_jpy.csv"),
    ("EUR_USD", ROOT / "data" / "llm_filter_decisions_eur_usd.csv"),
]:
    df = pd.read_csv(path)
    # クレジット切れエラー行を除外
    is_credit_err = df["llm_error"].fillna("").astype(str).str.contains("credit", case=False, na=False)
    clean = df[~is_credit_err].copy()

    # それ以外の API エラーが残っている行 (リトライで救えなかった分)
    has_api_err = clean["llm_error"].fillna("").astype(str).str.contains(
        "Error code|RateLimitError|APIError|APIStatusError|api_error", case=False, na=False
    )

    total_cost = clean["api_cost_usd"].sum()
    print(f"=== {pair} ===")
    print(f"  total rows in raw CSV: {len(df)}")
    print(f"  credit-exhaustion rows removed: {is_credit_err.sum()}")
    print(f"  clean rows: {len(clean)}")
    print(f"  of which still has non-credit API errors: {has_api_err.sum()}")
    print(f"  effective valid LLM decisions: {len(clean) - has_api_err.sum()}")
    print(f"  total cost in clean rows: ${total_cost:.4f}")
    print(f"  decision distribution (clean):")
    print(clean["llm_decision"].value_counts())
    out_path = path.with_name(path.stem + "_clean.csv")
    clean.to_csv(out_path, index=False)
    print(f"  saved clean CSV: {out_path}")
    print()
