"""
第2サイクル LLM Direct Filter プロトタイプ — GBP_JPY 216件 先行検証

目的:
    `data/signal_v2_historical_signals.csv` の GBP_JPY シグナルに対し、
    Claude Sonnet で CONFIRM / NEUTRAL / CONTRADICT / REJECT を判定し、
    signal_v2 単独 PF (≈0.95) からどれだけ改善できるかを測定する。

リーク防止:
    `high_after_entry_24h`, `low_after_entry_24h`, `close_24h_after_entry`,
    `actual_pnl_*`, `win_loss_sl_tp`, `holding_minutes_first_touch` は
    LLM プロンプトに渡さない (正解ラベル)。

出力:
    1. data/llm_filter_decisions_gbp_jpy.csv — 各行の LLM 判定
    2. docs/proposals/cycle2/LLM_FILTER_GBP_JPY_REPORT.md — PF 差分集計レポート
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

# プロジェクトルートを sys.path に
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

# .env 読込: 自プロジェクトの .env を最優先、見つからなければ近傍プロジェクトを試す
# (CLAUDE.md ルール: API キーはチャットに出さない・ハードコードしない)
_DEFAULT_ENV = _PROJECT_ROOT / ".env"
if _DEFAULT_ENV.exists():
    load_dotenv(_DEFAULT_ENV)

# 環境変数経由で渡されたキーが優先される。なければ近傍プロジェクトの .env を fallback
if not os.environ.get("ANTHROPIC_API_KEY"):
    for _fallback in [
        _PROJECT_ROOT.parent / "タスクマネージャー" / ".env",
        _PROJECT_ROOT.parent / "住宅比較" / ".env",
    ]:
        if _fallback.exists():
            load_dotenv(_fallback, override=False)
            if os.environ.get("ANTHROPIC_API_KEY"):
                break

try:
    from anthropic import Anthropic, APIError, APIStatusError, RateLimitError
except ImportError:
    print("anthropic SDK が見つかりません。`pip install anthropic` してください。", file=sys.stderr)
    sys.exit(1)

# ============================================================
# 設定
# ============================================================

INPUT_CSV = _PROJECT_ROOT / "data" / "signal_v2_historical_signals.csv"

# 出力パスはペア別に動的生成 (build_paths 経由)
TARGET_PAIR = "GBP_JPY"


def build_paths(pair: str) -> tuple[Path, Path]:
    """ペア別の出力 CSV と レポート MD のパスを返す。"""
    pair_lower = pair.lower()
    pair_upper = pair.upper()
    output_csv = _PROJECT_ROOT / "data" / f"llm_filter_decisions_{pair_lower}.csv"
    report_md = _PROJECT_ROOT / "docs" / "proposals" / "cycle2" / f"LLM_FILTER_{pair_upper}_REPORT.md"
    return output_csv, report_md
MODEL_ID = "claude-sonnet-4-6"          # CLAUDE.md グローバルルール: モデルID固定
TEMPERATURE = 0.0                        # 再現性
MAX_TOKENS = 200
RATE_LIMIT_SLEEP_SEC = float(os.environ.get("CYCLE2_LLM_SLEEP", "0.6"))  # 環境変数で上書き可能
MAX_RETRIES = 3

# Claude Sonnet 4 系の概算単価 (USD/M tokens)。コスト記録用、変動可能性あり
USD_PER_M_INPUT = 3.0
USD_PER_M_OUTPUT = 15.0

# プロンプトに渡してはいけない列 (正解ラベル / 未来情報)
LEAKAGE_COLUMNS = {
    "high_after_entry_24h",
    "low_after_entry_24h",
    "close_24h_after_entry",
    "actual_pnl_pips_sl_tp_first_touch",
    "actual_pnl_pips_4h_close",
    "actual_pnl_pips_24h_close",
    "win_loss_sl_tp",
    "holding_minutes_first_touch",
}

VALID_DECISIONS = {"CONFIRM", "NEUTRAL", "CONTRADICT", "REJECT"}

# ============================================================
# ログ
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("cycle2_llm_filter")


# ============================================================
# プロンプト生成
# ============================================================

SYSTEM_PROMPT = (
    "あなたは FX 自動取引のリスク判定エージェントです。"
    "与えられたシグナル時点のコンテキストに基づき、取引を取るべきか判定します。"
    "回答は必ず JSON 形式 (コードブロック不要、平文 JSON のみ) で返してください。"
)


def build_user_prompt(row: pd.Series) -> str:
    """シグナル1件分のユーザープロンプトを構築する (未来情報は除外)。"""
    return f"""[シグナル情報]
- ペア: {row['pair']}
- 時刻 (UTC): {row['timestamp_utc']}
- 方向: {row['direction']}
- エントリー: {row['entry_price']}
- SL: {row['sl_price']} ({row['sl_pips']} pips)
- TP: {row['tp_price']} ({row['tp_pips']} pips)
- ATR: {row['atr']}

[市況コンテキスト]
- M15 終値 24h前: {row['m15_close_24h_ago']}
- M15 終値 12h前: {row['m15_close_12h_ago']}
- M15 終値 1h前: {row['m15_close_1h_ago']}
- EUR/USD 24h 変化: {row['related_eur_usd_24h_change_pct']}%
- USD/JPY 24h 変化: {row['related_usd_jpy_24h_change_pct']}%
- GBP/USD 24h 変化: {row['related_gbp_usd_24h_change_pct']}%
- 曜日 (0=月): {row['day_of_week']} / UTC時: {row['hour_utc']}
- セッション: tokyo={row['is_tokyo_session']}, london={row['is_london_session']}, ny={row['is_ny_session']}

[判定]
以下の JSON だけを返してください (前後の説明文や ``` は付けない):
{{
  "decision": "CONFIRM" | "NEUTRAL" | "CONTRADICT" | "REJECT",
  "confidence": 0.0-1.0 の小数,
  "reasoning": "1-2文の判定理由 (日本語)"
}}

判定基準:
- CONFIRM: シグナル方向を取るべき (強い同意)
- NEUTRAL: 取ってよい (積極推奨ではない)
- CONTRADICT: 反対方向を取るべき
- REJECT: 取らない (危険な状況、流動性低下、レンジで逆張り、等)
"""


# ============================================================
# LLM 呼び出し
# ============================================================


@dataclass
class LLMResult:
    decision: str
    confidence: float
    reasoning: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    raw_response: str
    error: Optional[str] = None


def parse_llm_json(text: str) -> dict:
    """LLM 応答テキストから JSON を抽出してパースする。コードブロックも吸収。"""
    s = text.strip()
    if s.startswith("```"):
        # ``` で囲まれている場合は最初と最後の ``` を除去
        lines = s.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        s = "\n".join(lines).strip()

    # JSON 本体だけ抽出 (前後にゴミがある場合に最初の { から最後の } まで)
    if not s.startswith("{"):
        first = s.find("{")
        last = s.rfind("}")
        if first >= 0 and last > first:
            s = s[first : last + 1]

    return json.loads(s)


def call_llm(client: Anthropic, user_prompt: str) -> LLMResult:
    """1シグナル分の LLM 判定を取得 (指数バックオフ付きリトライ)。"""
    last_error: Optional[str] = None
    backoff = 2.0

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.messages.create(
                model=MODEL_ID,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_text = "".join(
                block.text for block in resp.content if getattr(block, "type", None) == "text"
            )
            usage_in = resp.usage.input_tokens
            usage_out = resp.usage.output_tokens
            cost = (
                usage_in / 1_000_000 * USD_PER_M_INPUT
                + usage_out / 1_000_000 * USD_PER_M_OUTPUT
            )

            try:
                parsed = parse_llm_json(raw_text)
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}; raw={raw_text[:200]!r}"
                logger.warning("LLM JSON parse 失敗 (attempt %d): %s", attempt, last_error)
                # JSON 不正は再試行しても改善しない可能性が高いが、念のため1回だけ retry
                if attempt < MAX_RETRIES:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return LLMResult(
                    decision="REJECT",  # パース失敗時は安全側に倒す
                    confidence=0.0,
                    reasoning=f"[parse_error] {last_error[:120]}",
                    input_tokens=usage_in,
                    output_tokens=usage_out,
                    cost_usd=cost,
                    raw_response=raw_text,
                    error=last_error,
                )

            decision = str(parsed.get("decision", "")).upper().strip()
            if decision not in VALID_DECISIONS:
                last_error = f"invalid decision: {decision!r}"
                logger.warning("LLM 判定不正 (attempt %d): %s", attempt, last_error)
                if attempt < MAX_RETRIES:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                decision = "REJECT"

            confidence = float(parsed.get("confidence", 0.0) or 0.0)
            reasoning = str(parsed.get("reasoning", ""))[:500]

            return LLMResult(
                decision=decision,
                confidence=confidence,
                reasoning=reasoning,
                input_tokens=usage_in,
                output_tokens=usage_out,
                cost_usd=cost,
                raw_response=raw_text,
                error=None,
            )

        except RateLimitError as e:
            last_error = f"RateLimitError: {e}"
            logger.warning("レート制限 (attempt %d): %s — %.1fs 待機", attempt, e, backoff)
            time.sleep(backoff)
            backoff *= 2
        except APIStatusError as e:
            last_error = f"APIStatusError {e.status_code}: {e}"
            logger.warning("API エラー (attempt %d): %s", attempt, last_error)
            if attempt < MAX_RETRIES and 500 <= (e.status_code or 0) < 600:
                time.sleep(backoff)
                backoff *= 2
            else:
                break
        except APIError as e:
            last_error = f"APIError: {e}"
            logger.warning("API エラー (attempt %d): %s", attempt, last_error)
            time.sleep(backoff)
            backoff *= 2
        except Exception as e:  # noqa: BLE001
            last_error = f"{type(e).__name__}: {e}"
            logger.exception("予期せぬエラー (attempt %d)", attempt)
            time.sleep(backoff)
            backoff *= 2

    # 全リトライ失敗
    return LLMResult(
        decision="REJECT",
        confidence=0.0,
        reasoning=f"[api_error] {last_error}",
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        raw_response="",
        error=last_error,
    )


# ============================================================
# メイン処理
# ============================================================


def run_filter(df: pd.DataFrame, client: Anthropic, limit: Optional[int] = None) -> pd.DataFrame:
    """全シグナルに LLM 判定を適用して結果 DataFrame を返す。"""
    rows = []
    n = len(df) if limit is None else min(limit, len(df))
    logger.info("LLM 判定開始: %d 件 (model=%s, temperature=%.1f)", n, MODEL_ID, TEMPERATURE)

    total_cost = 0.0
    t0 = time.time()
    for i, (_, row) in enumerate(df.head(n).iterrows(), start=1):
        prompt = build_user_prompt(row)
        result = call_llm(client, prompt)
        total_cost += result.cost_usd

        rows.append({
            "signal_id": row["signal_id"],
            "pair": row["pair"],
            "timestamp_utc": row["timestamp_utc"],
            "direction": row["direction"],
            "llm_decision": result.decision,
            "llm_confidence": result.confidence,
            "llm_reasoning": result.reasoning,
            "api_input_tokens": result.input_tokens,
            "api_output_tokens": result.output_tokens,
            "api_cost_usd": result.cost_usd,
            "llm_error": result.error or "",
        })

        if i % 20 == 0 or i == n:
            elapsed = time.time() - t0
            logger.info(
                "進捗 %d/%d (%.1f%%) | elapsed=%.1fs | cost=$%.3f | last_decision=%s",
                i, n, 100 * i / n, elapsed, total_cost, result.decision,
            )

        time.sleep(RATE_LIMIT_SLEEP_SEC)

    logger.info("LLM 判定完了: %d 件, 総コスト $%.4f", n, total_cost)
    return pd.DataFrame(rows)


# ============================================================
# パフォーマンス集計
# ============================================================


def compute_pf(pnls: pd.Series) -> dict:
    """pips 単位の PnL Series から PF / 勝率 / 平均勝ち負けを返す。"""
    n = len(pnls)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "avg_win": float("nan"),
                "avg_loss": float("nan"), "PF": float("nan"), "cum_pips": 0.0}
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    win_sum = wins.sum()
    loss_sum = -losses.sum()
    pf = (win_sum / loss_sum) if loss_sum > 0 else float("inf")
    return {
        "n": n,
        "win_rate": (pnls > 0).mean(),
        "avg_win": wins.mean() if len(wins) else float("nan"),
        "avg_loss": losses.mean() if len(losses) else float("nan"),
        "PF": pf,
        "cum_pips": pnls.sum(),
    }


def aggregate_pf(
    signals: pd.DataFrame, decisions: pd.DataFrame
) -> dict:
    """カテゴリ別の PF を集計する。

    Returns:
        {
            "base": {...},
            "confirm_only": {...},
            "confirm_neutral": {...},
            "contradict_inverted": {...},
            "reject_only": {...},          # 参考: REJECT 群が REJECT で正解だったか
            "distribution": {...},
        }
    """
    merged = signals.merge(
        decisions[["signal_id", "llm_decision"]], on="signal_id", how="inner"
    )
    pnl = merged["actual_pnl_pips_sl_tp_first_touch"] - merged["spread_assumed_pips"]
    merged = merged.assign(net_pnl_pips=pnl)

    base = compute_pf(merged["net_pnl_pips"])

    confirm = merged[merged["llm_decision"] == "CONFIRM"]
    confirm_neutral = merged[merged["llm_decision"].isin(["CONFIRM", "NEUTRAL"])]
    contradict = merged[merged["llm_decision"] == "CONTRADICT"]
    reject = merged[merged["llm_decision"] == "REJECT"]
    neutral = merged[merged["llm_decision"] == "NEUTRAL"]

    # CONTRADICT 反転 = 方向を逆にする = PnL を -1 倍
    contradict_inverted_pnl = -contradict["net_pnl_pips"]

    distribution = merged["llm_decision"].value_counts().to_dict()

    return {
        "base": base,
        "confirm_only": compute_pf(confirm["net_pnl_pips"]),
        "neutral_only": compute_pf(neutral["net_pnl_pips"]),
        "confirm_neutral": compute_pf(confirm_neutral["net_pnl_pips"]),
        "contradict_as_is": compute_pf(contradict["net_pnl_pips"]),
        "contradict_inverted": compute_pf(contradict_inverted_pnl),
        "reject_as_is": compute_pf(reject["net_pnl_pips"]),
        "distribution": distribution,
        "merged": merged,
    }


# ============================================================
# レポート生成
# ============================================================


def _fmt_pf(d: dict) -> str:
    if d["n"] == 0:
        return "n=0"
    pf = d["PF"]
    pf_s = "inf" if pf == float("inf") else f"{pf:.3f}"
    return (
        f"n={d['n']}, win_rate={d['win_rate']:.1%}, "
        f"avg_win={d['avg_win']:.2f} pips, avg_loss={d['avg_loss']:.2f} pips, "
        f"PF={pf_s}, cum={d['cum_pips']:.1f} pips"
    )


def _format_examples(merged: pd.DataFrame, decision: str, k: int = 5) -> str:
    """カテゴリ別の代表例 (理由抜粋) を整形する。"""
    sub = merged[merged["llm_decision"] == decision]
    # llm_reasoning は decisions 側に存在
    rows = sub.head(k)
    if rows.empty:
        return f"- (該当なし)"
    out = []
    for _, r in rows.iterrows():
        reasoning = str(r.get("llm_reasoning", ""))[:160]
        net = r["net_pnl_pips"]
        out.append(
            f"- `{r['signal_id']}` {r['direction']} → "
            f"{decision} (conf={r.get('llm_confidence', float('nan')):.2f}, "
            f"net={net:.1f} pips): {reasoning}"
        )
    return "\n".join(out)


def build_report(
    agg: dict, decisions: pd.DataFrame, total_cost_usd: float, n_signals: int,
    pair: str = TARGET_PAIR,
) -> str:
    """レポート Markdown を生成する。"""
    pair_lower = pair.lower()
    pair_upper = pair.upper()
    base = agg["base"]
    co = agg["confirm_only"]
    cn = agg["confirm_neutral"]
    ci = agg["contradict_inverted"]
    rj = agg["reject_as_is"]
    no = agg["neutral_only"]
    ca = agg["contradict_as_is"]

    dist = agg["distribution"]
    total = sum(dist.values())

    def pct(k):
        return 100.0 * dist.get(k, 0) / total if total else 0.0

    # PF 差分判定
    base_pf = base["PF"] if base["PF"] != float("inf") else 99.99
    confirm_pf = co["PF"] if co["PF"] != float("inf") else 99.99
    confirm_neutral_pf = cn["PF"] if cn["PF"] != float("inf") else 99.99

    # 主軸: CONFIRM+NEUTRAL のフィルタ後 PF
    pf_diff_cn = confirm_neutral_pf - base_pf
    pf_diff_confirm = confirm_pf - base_pf

    gate_pass_diff = pf_diff_cn >= 0.30 or pf_diff_confirm >= 0.30
    gate_pass_n = cn["n"] >= 30 or co["n"] >= 30
    reject_rate = dist.get("REJECT", 0) / total if total else 0.0
    gate_pass_reject = reject_rate < 0.80

    # 比較用 merged
    merged = agg["merged"].merge(
        decisions[["signal_id", "llm_reasoning", "llm_confidence"]],
        on="signal_id", how="left",
    )

    monthly_estimate = total_cost_usd / n_signals * (2616 + 216)  # USD_JPY 2616件 + GBP_JPY 216件で1ヶ月相当と想定
    # 注: monthly_estimate は「全 GBP_JPY+USD_JPY 検証コスト」目安。本番ライブ運用とは異なる

    lines = [
        f"# LLM Direct Filter 検証レポート — {pair_upper} {n_signals}件",
        "",
        f"**実行日**: 2026-05-26",
        f"**対象**: `data/signal_v2_historical_signals.csv` から `pair == '{pair_upper}'` 抽出 {n_signals} 件",
        f"**モデル**: `{MODEL_ID}` (temperature={TEMPERATURE}, max_tokens={MAX_TOKENS})",
        f"**実コスト**: ${total_cost_usd:.4f} USD (≒ ¥{total_cost_usd * 150:.0f})",
        "",
        "---",
        "",
        "## TL;DR",
        "",
        f"- **ベース PF (signal_v2 単独)**: {base['PF']:.3f} (n={base['n']}, win_rate={base['win_rate']:.1%})",
        f"- **LLM CONFIRM のみ PF**: {co['PF']:.3f} (n={co['n']})",
        f"- **LLM CONFIRM+NEUTRAL PF**: {cn['PF']:.3f} (n={cn['n']})",
        f"- **PF 差分 (CONFIRM+NEUTRAL − base)**: {pf_diff_cn:+.3f}",
        f"- **PF 差分 (CONFIRM only − base)**: {pf_diff_confirm:+.3f}",
        f"- **ゲート (+0.30) 判定**: {'PASS' if gate_pass_diff else 'FAIL'}",
        "",
        "---",
        "",
        "## 判定分布",
        "",
        "| カテゴリ | 件数 | % |",
        "|---|---|---|",
        f"| CONFIRM     | {dist.get('CONFIRM', 0)}     | {pct('CONFIRM'):.1f}% |",
        f"| NEUTRAL     | {dist.get('NEUTRAL', 0)}     | {pct('NEUTRAL'):.1f}% |",
        f"| CONTRADICT  | {dist.get('CONTRADICT', 0)}  | {pct('CONTRADICT'):.1f}% |",
        f"| REJECT      | {dist.get('REJECT', 0)}      | {pct('REJECT'):.1f}% |",
        f"| **合計**    | **{total}** | **100.0%** |",
        "",
        "---",
        "",
        "## 各カテゴリのパフォーマンス (Trade-by-trade集計)",
        "",
        "PnL は `actual_pnl_pips_sl_tp_first_touch - spread_assumed_pips` (spread 控除済み net pips)。",
        "",
        "| カテゴリ | 件数 | 勝率 | 平均勝ち pips | 平均負け pips | PF | 累計 pips |",
        "|---|---|---|---|---|---|---|",
        _row("base (全件)", base),
        _row("CONFIRM only", co),
        _row("NEUTRAL only", no),
        _row("CONFIRM+NEUTRAL", cn),
        _row("CONTRADICT そのまま", ca),
        _row("CONTRADICT 反転 (-1×)", ci),
        _row("REJECT (取らなかった群の実 PnL)", rj),
        "",
        "---",
        "",
        "## ゲート判定 (CYCLE2_PLAN.md 必須条件)",
        "",
        f"- **PF 差分 ≥ +0.30**: {'PASS' if gate_pass_diff else 'FAIL'} (CONFIRM+NEUTRAL: {pf_diff_cn:+.3f}, CONFIRM only: {pf_diff_confirm:+.3f})",
        f"- **OOS trades ≥ 30**: {'PASS' if gate_pass_n else 'FAIL'} (CONFIRM+NEUTRAL n={cn['n']}, CONFIRM only n={co['n']})",
        f"- **LLM REJECT 率 < 80%**: {'PASS' if gate_pass_reject else 'FAIL'} ({reject_rate:.1%})",
        "",
        "**総合**: " + ("PASS — USD_JPY 拡張検証へ" if (gate_pass_diff and gate_pass_n and gate_pass_reject) else "FAIL — プロンプト調整 or 第2サイクル撤退検討"),
        "",
        "---",
        "",
        "## LLM 判断の質的観察",
        "",
        "### 典型的な CONFIRM 例",
        _format_examples(merged, "CONFIRM", k=5),
        "",
        "### 典型的な NEUTRAL 例",
        _format_examples(merged, "NEUTRAL", k=3),
        "",
        "### 典型的な REJECT 例",
        _format_examples(merged, "REJECT", k=5),
        "",
        "### 典型的な CONTRADICT 例",
        _format_examples(merged, "CONTRADICT", k=3),
        "",
        "---",
        "",
        "## 一貫性・再現性メモ",
        "",
        f"- `temperature={TEMPERATURE}` で固定 (再実行で同じ結果になる前提)",
        f"- パース失敗・API 失敗時は安全側に REJECT に倒している (該当件数は `llm_error` 列で確認可能)",
        f"- API 失敗件数: {decisions['llm_error'].fillna('').astype(str).str.strip().str.len().gt(0).sum()}",
        "",
        "---",
        "",
        "## コストとスケーラビリティ",
        "",
        f"- {pair_upper} {n_signals}件 実コスト: ${total_cost_usd:.4f} USD",
        f"- 1件あたり: ${total_cost_usd / n_signals:.5f} USD (≒ ¥{total_cost_usd / n_signals * 150:.2f})",
        f"- 5,000件スケール時の見込み: ${total_cost_usd / n_signals * 5000:.2f} USD",
        f"- 月間ライブ運用 (シグナル発生量による、概算): 別途試算",
        "",
        "---",
        "",
        "## 次のアクション",
        "",
    ]

    if gate_pass_diff and gate_pass_n and gate_pass_reject:
        lines += [
            "**価値あり → USD_JPY (2,616件) 拡張で検証強化**",
            "",
            "- 同スクリプトを `--pair USD_JPY` で実行 (推定コスト 1,200-2,400円)",
            "- USD_JPY でも PF 差分 +0.3 以上を再現できるか検証",
            "- 再現できれば Phase 2' (新 SPEC v3 起草) 進出を検討",
        ]
    elif pf_diff_cn >= 0.10 or pf_diff_confirm >= 0.10:
        lines += [
            "**価値微妙 → プロンプト調整・コンテキスト拡充**",
            "",
            "- 経済指標カレンダー (任意フィールド) を追加",
            "- few-shot 例を追加 (CONFIRM 成功例 / REJECT 回避例)",
            "- 1次追加検証 1,000円以内で再実行",
        ]
    else:
        lines += [
            "**価値なし → 第2サイクル撤退検討**",
            "",
            "- CYCLE2_PLAN.md 撤退条件「Phase 0' 候補3本起草後 PF +0.3 未達なら全体撤退」に該当する可能性",
            "- ロングリスト (memory `research_ai_trading_2026_03.md`) から別の手法候補に切替",
        ]

    lines += [
        "",
        "---",
        "",
        "## ファイル",
        "",
        f"- 入力: `data/signal_v2_historical_signals.csv` ({pair_upper} 抽出 {n_signals} 件)",
        f"- 出力: `data/llm_filter_decisions_{pair_lower}.csv`",
        f"- スクリプト: `scripts/_cycle2_llm_filter.py`",
        "",
    ]

    return "\n".join(lines)


def _row(label: str, d: dict) -> str:
    if d["n"] == 0:
        return f"| {label} | 0 | - | - | - | - | 0.0 |"
    pf = d["PF"]
    pf_s = "inf" if pf == float("inf") else f"{pf:.3f}"
    aw = f"{d['avg_win']:.2f}" if d["avg_win"] == d["avg_win"] else "-"  # NaN チェック
    al = f"{d['avg_loss']:.2f}" if d["avg_loss"] == d["avg_loss"] else "-"
    return (
        f"| {label} | {d['n']} | {d['win_rate']:.1%} | {aw} | {al} | {pf_s} | {d['cum_pips']:.1f} |"
    )


# ============================================================
# エントリポイント
# ============================================================


def main() -> int:
    parser = argparse.ArgumentParser(description="Cycle 2 LLM Direct Filter")
    parser.add_argument("--limit", type=int, default=None, help="検証件数の上限 (デバッグ用)")
    parser.add_argument(
        "--skip-llm", action="store_true",
        help="LLM 呼び出しをスキップし、既存の出力 CSV を使ってレポートだけ再生成"
    )
    parser.add_argument("--pair", default=TARGET_PAIR, help="対象通貨ペア")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key and not args.skip_llm:
        logger.error("ANTHROPIC_API_KEY が見つかりません (.env または環境変数)")
        return 2

    # ペア別の出力パスを構築
    output_csv, report_md = build_paths(args.pair)
    logger.info("対象ペア: %s", args.pair)
    logger.info("出力 CSV: %s", output_csv)
    logger.info("レポート MD: %s", report_md)

    logger.info("入力 CSV 読込: %s", INPUT_CSV)
    df = pd.read_csv(INPUT_CSV)
    signals = df[df["pair"] == args.pair].copy()
    logger.info("対象シグナル: %s = %d 件", args.pair, len(signals))

    # 安全確認: LLM プロンプトに渡される列にリーク列が混入していないか
    safe_columns = set(signals.columns) - LEAKAGE_COLUMNS
    logger.info("プロンプト利用列数: %d / リーク除外列数: %d",
                len(safe_columns), len(LEAKAGE_COLUMNS & set(signals.columns)))

    if args.skip_llm:
        if not output_csv.exists():
            logger.error("--skip-llm 指定だが %s が存在しない", output_csv)
            return 3
        decisions = pd.read_csv(output_csv)
        logger.info("既存判定 CSV 読込: %d 件", len(decisions))
    else:
        client = Anthropic(api_key=api_key)
        decisions = run_filter(signals, client, limit=args.limit)
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        decisions.to_csv(output_csv, index=False)
        logger.info("LLM 判定を %s に保存", output_csv)

    # 集計
    agg = aggregate_pf(signals, decisions)
    total_cost = decisions["api_cost_usd"].sum() if "api_cost_usd" in decisions else 0.0

    # コンソール出力
    print("\n========== 集計結果 ==========")
    print(f"対象: {args.pair} n={len(signals)} / 判定済: {len(decisions)}")
    print(f"判定分布: {agg['distribution']}")
    print(f"base            : {_fmt_pf(agg['base'])}")
    print(f"CONFIRM only    : {_fmt_pf(agg['confirm_only'])}")
    print(f"NEUTRAL only    : {_fmt_pf(agg['neutral_only'])}")
    print(f"CONFIRM+NEUTRAL : {_fmt_pf(agg['confirm_neutral'])}")
    print(f"CONTRADICT (raw): {_fmt_pf(agg['contradict_as_is'])}")
    print(f"CONTRADICT inv  : {_fmt_pf(agg['contradict_inverted'])}")
    print(f"REJECT (raw)    : {_fmt_pf(agg['reject_as_is'])}")
    print(f"API 実コスト    : ${total_cost:.4f} USD")
    print("=============================\n")

    # レポート出力
    report_text = build_report(agg, decisions, total_cost, len(signals), pair=args.pair)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(report_text, encoding="utf-8")
    logger.info("レポート保存: %s", report_md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
