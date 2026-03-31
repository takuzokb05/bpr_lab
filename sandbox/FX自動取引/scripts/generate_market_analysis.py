"""
FX自動取引システム — 日次AI市場環境分析スクリプト

Windows VPS上でMT5から直接価格データを取得し、
Claude APIで市場環境を分析してdata/market_analysis.jsonに書き出す。
オプションでSlack Webhookにレポートを投稿する。

タスクスケジューラで日次実行（JST 6:30）:
  schtasks /Create /TN "FX_MarketAnalysis" ^
    /TR "cmd.exe /c cd /d C:\\bpr_lab\\fx_trading && python scripts/generate_market_analysis.py" ^
    /SC DAILY /ST 06:30 /RL HIGHEST /F

プロンプト設計7鉄則準拠:
  1. 生OHLCVではなく加工済み指標を渡す
  2. 出力はJSON固定
  3. ロール設定が効く
  4. リスクルールはプロンプトに明示
  5. Dual-AI検証（将来対応）
  6. 逆張りプロンプト（リスク要因を列挙させる）
  7. コンテキスト先行
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# プロジェクトルートをsys.pathに追加
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

import pandas as pd
import pandas_ta as ta
import requests

import os

from dotenv import load_dotenv

# .env読み込み（FXプロジェクト用）
load_dotenv(_project_root / ".env")

from src.config import (
    ADX_PERIOD,
    AI_MODEL_ID,
    ANTHROPIC_API_KEY,
    ATR_PERIOD,
    MA_LONG_PERIOD,
    MA_SHORT_PERIOD,
    MFI_PERIOD,
    RSI_PERIOD,
    SLACK_WEBHOOK_URL,
)

logger = logging.getLogger(__name__)

# 分析対象の通貨ペア
DEFAULT_INSTRUMENT = "USD_JPY"

# MT5シンボル接尾辞（外為ファイネスト）
MT5_SUFFIX = "-"

# Claude API
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_API_TIMEOUT = 60

# SocialData API
SOCIALDATA_API_KEY = os.getenv("SOCIALDATA_API_KEY", "")
SOCIALDATA_API_URL = "https://api.socialdata.tools/twitter/search"
SOCIALDATA_TIMEOUT = 30


# ============================================================
# MT5 データ取得
# ============================================================


def fetch_mt5_data(
    symbol: str, timeframe_h4: int = 100, timeframe_d1: int = 30
) -> dict:
    """
    MT5から価格データを取得してテクニカル指標を計算する。

    Args:
        symbol: 通貨ペア（例: "USD_JPY"）
        timeframe_h4: H4足の取得本数
        timeframe_d1: D1足の取得本数

    Returns:
        テクニカル指標の辞書
    """
    import MetaTrader5 as mt5

    if not mt5.initialize():
        raise RuntimeError(f"MT5初期化失敗: {mt5.last_error()}")

    try:
        mt5_symbol = symbol.replace("_", "") + MT5_SUFFIX

        # H4データ取得
        h4_rates = mt5.copy_rates_from_pos(
            mt5_symbol, mt5.TIMEFRAME_H4, 0, timeframe_h4
        )
        if h4_rates is None or len(h4_rates) == 0:
            raise RuntimeError(f"H4データ取得失敗: {mt5_symbol}")

        h4_df = pd.DataFrame(h4_rates)
        h4_df.columns = [c.lower() for c in h4_df.columns]
        # MT5のtick_volumeをvolumeとして使用
        if "tick_volume" in h4_df.columns and "volume" not in h4_df.columns:
            h4_df["volume"] = h4_df["tick_volume"]

        # D1データ取得
        d1_rates = mt5.copy_rates_from_pos(
            mt5_symbol, mt5.TIMEFRAME_D1, 0, timeframe_d1
        )
        if d1_rates is None or len(d1_rates) == 0:
            raise RuntimeError(f"D1データ取得失敗: {mt5_symbol}")

        d1_df = pd.DataFrame(d1_rates)
        d1_df.columns = [c.lower() for c in d1_df.columns]
        if "tick_volume" in d1_df.columns and "volume" not in d1_df.columns:
            d1_df["volume"] = d1_df["tick_volume"]

        # テクニカル指標計算
        indicators = _calculate_indicators(h4_df, d1_df, symbol)
        return indicators

    finally:
        mt5.shutdown()


def _calculate_indicators(
    h4: pd.DataFrame, d1: pd.DataFrame, instrument: str
) -> dict:
    """H4/D1データからテクニカル指標を計算する。"""

    # --- H4 指標 ---
    rsi = ta.rsi(h4["close"], length=RSI_PERIOD)
    adx_df = ta.adx(h4["high"], h4["low"], h4["close"], length=ADX_PERIOD)
    atr = ta.atr(h4["high"], h4["low"], h4["close"], length=ATR_PERIOD)
    ma_short = ta.sma(h4["close"], length=MA_SHORT_PERIOD)
    ma_long = ta.sma(h4["close"], length=MA_LONG_PERIOD)
    bbands = ta.bbands(h4["close"], length=20, std=2.0)

    # MFI（volume列がある場合のみ）
    mfi_val = None
    if "volume" in h4.columns:
        mfi = ta.mfi(
            h4["high"], h4["low"], h4["close"], h4["volume"], length=MFI_PERIOD
        )
        if mfi is not None and not mfi.empty:
            mfi_val = _safe_last(mfi)

    # BBW比率
    bbw_ratio = None
    if bbands is not None:
        bbw_candidates = [c for c in bbands.columns if c.startswith("BBB_")]
        if bbw_candidates:
            bbw = bbands[bbw_candidates[0]].dropna()
            if len(bbw) >= 2:
                bbw_ratio = round(float(bbw.iloc[-1] / bbw.mean()), 3)

    # MA位置関係
    ma_s = _safe_last(ma_short)
    ma_l = _safe_last(ma_long)
    if ma_s is not None and ma_l is not None:
        if ma_s > ma_l:
            ma_position = "短期>長期（上昇トレンド示唆）"
        elif ma_s < ma_l:
            ma_position = "短期<長期（下降トレンド示唆）"
        else:
            ma_position = "ほぼ一致（方向性なし）"
    else:
        ma_position = "計算不能"

    # ADX値
    adx_val = None
    if adx_df is not None:
        adx_col = f"ADX_{ADX_PERIOD}"
        if adx_col in adx_df.columns:
            adx_val = _safe_last(adx_df[adx_col])

    # レジーム簡易判定
    if adx_val is not None:
        if adx_val >= 25:
            regime = "trending"
        elif adx_val < 20:
            regime = "ranging"
        else:
            regime = "transitional"
    else:
        regime = "unknown"

    # --- D1 指標 ---
    d1_rsi = ta.rsi(d1["close"], length=RSI_PERIOD)
    d1_adx_df = ta.adx(d1["high"], d1["low"], d1["close"], length=ADX_PERIOD)
    d1_ma_long = ta.sma(d1["close"], length=MA_LONG_PERIOD)

    d1_adx_val = None
    if d1_adx_df is not None:
        d1_adx_col = f"ADX_{ADX_PERIOD}"
        if d1_adx_col in d1_adx_df.columns:
            d1_adx_val = _safe_last(d1_adx_df[d1_adx_col])

    # D1トレンド方向
    d1_ma_l = d1_ma_long.iloc[-1] if d1_ma_long is not None and not d1_ma_long.empty else None
    d1_ma_l_prev = d1_ma_long.iloc[-2] if d1_ma_long is not None and len(d1_ma_long) >= 2 else None
    if d1_ma_l is not None and d1_ma_l_prev is not None:
        if not pd.isna(d1_ma_l) and not pd.isna(d1_ma_l_prev):
            slope = d1_ma_l - d1_ma_l_prev
            if slope > 0:
                d1_trend = "上昇"
            elif slope < 0:
                d1_trend = "下降"
            else:
                d1_trend = "横ばい"
        else:
            d1_trend = "不明"
    else:
        d1_trend = "不明"

    return {
        "instrument": instrument,
        "timeframe": "H4",
        "last_close": round(float(h4["close"].iloc[-1]), 5),
        "indicators": {
            "rsi_14": _round(rsi),
            "adx_14": _round_val(adx_val),
            "atr_14": _round(atr, 5),
            "mfi_14": _round_val(mfi_val),
            "ma_20": _round(ma_short, 3),
            "ma_50": _round(ma_long, 3),
            "ma_position": ma_position,
            "bbw_ratio": bbw_ratio,
            "regime": regime,
        },
        "daily_context": {
            "d1_rsi": _round(d1_rsi),
            "d1_adx": _round_val(d1_adx_val),
            "d1_trend": d1_trend,
        },
    }


def _safe_last(series) -> float | None:
    """Seriesの最後の有効値を返す。NaNや空の場合はNone。"""
    if series is None or series.empty:
        return None
    val = series.iloc[-1]
    if pd.isna(val):
        return None
    return float(val)


def _round(series, digits: int = 1) -> float | None:
    """Seriesの最後の値を丸めて返す。"""
    val = _safe_last(series)
    if val is None:
        return None
    return round(val, digits)


def _round_val(val: float | None, digits: int = 1) -> float | None:
    """値を丸めて返す。"""
    if val is None:
        return None
    return round(val, digits)


# ============================================================
# 情報収集レイヤー（FinMem浅層 + @loopdomナラティブ）
# ============================================================


def fetch_market_sentiment(instrument: str = "USD_JPY", max_tweets: int = 10) -> list[dict]:
    """
    SocialData APIでX上の直近の市場センチメントを取得する。

    @loopdomの「市場はナラティブで動く」に基づき、
    トレーダーたちが今何を語っているかを収集する。

    Args:
        instrument: 通貨ペア
        max_tweets: 取得上限

    Returns:
        投稿リスト [{"text": str, "faves": int, "handle": str, "date": str}, ...]
    """
    if not SOCIALDATA_API_KEY:
        logger.info("SOCIALDATA_API_KEY未設定のためセンチメント取得スキップ")
        return []

    # 通貨ペアに応じたクエリ
    query_map = {
        "USD_JPY": [
            '(USDJPY OR "ドル円" OR "USD/JPY") (FX OR forex OR 為替) min_faves:10 lang:ja -is:retweet within_time:1d',
            '(USDJPY OR "USD/JPY") (analysis OR outlook OR forecast) min_faves:20 lang:en -is:retweet within_time:1d',
        ],
        "EUR_USD": [
            '(EURUSD OR "EUR/USD") (analysis OR outlook) min_faves:20 lang:en -is:retweet within_time:1d',
        ],
    }

    queries = query_map.get(instrument, [
        f'("{instrument.replace("_", "/")}" OR {instrument.replace("_", "")}) forex min_faves:10 -is:retweet within_time:1d',
    ])

    headers = {"Authorization": f"Bearer {SOCIALDATA_API_KEY}"}
    tweets = []

    for q in queries:
        try:
            resp = requests.get(
                SOCIALDATA_API_URL,
                params={"query": q, "type": "Latest"},
                headers=headers,
                timeout=SOCIALDATA_TIMEOUT,
            )
            if resp.status_code != 200:
                logger.warning("SocialData APIエラー (HTTP %d): %s", resp.status_code, resp.text[:100])
                continue

            data = resp.json()
            for tweet in data.get("tweets", []):
                tweets.append({
                    "text": tweet.get("full_text", tweet.get("text", "")),
                    "faves": tweet.get("favorite_count", 0),
                    "handle": tweet.get("user", {}).get("screen_name", ""),
                    "followers": tweet.get("user", {}).get("followers_count", 0),
                    "date": tweet.get("created_at", ""),
                })

        except requests.exceptions.Timeout:
            logger.warning("SocialData APIタイムアウト")
        except Exception as e:
            logger.warning("SocialData APIエラー: %s", e)

    # いいね数でソートし上位N件
    tweets.sort(key=lambda t: t["faves"], reverse=True)
    result = tweets[:max_tweets]
    logger.info("市場センチメント取得: %d件（全%d件中）", len(result), len(tweets))
    return result


def fetch_economic_calendar() -> list[dict]:
    """
    本日の経済イベントを取得する。

    FOMC、雇用統計、GDP等の重要イベントがある日は
    レンジ戦略の精度が下がるため、AIにリスク要因として渡す。

    Returns:
        イベントリスト [{"time": str, "event": str, "impact": str, "currency": str}, ...]
    """
    # Forex Factory等のスクレイピングは脆いので、
    # 無料APIとしてTrading Economics風のアプローチを取る
    # ここではSocialData APIで経済イベント関連投稿を代替取得
    if not SOCIALDATA_API_KEY:
        logger.info("SOCIALDATA_API_KEY未設定のため経済カレンダー取得スキップ")
        return []

    today = datetime.now().strftime("%Y-%m-%d")
    queries = [
        f'("経済指標" OR "重要指標") (FOMC OR 雇用統計 OR CPI OR GDP OR 日銀 OR BOJ OR FRB) min_faves:5 -is:retweet within_time:1d',
        f'(FOMC OR "nonfarm" OR CPI OR "rate decision") forex "today" min_faves:10 lang:en -is:retweet within_time:1d',
    ]

    headers = {"Authorization": f"Bearer {SOCIALDATA_API_KEY}"}
    events = []

    for q in queries:
        try:
            resp = requests.get(
                SOCIALDATA_API_URL,
                params={"query": q, "type": "Latest"},
                headers=headers,
                timeout=SOCIALDATA_TIMEOUT,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            for tweet in data.get("tweets", []):
                text = tweet.get("full_text", tweet.get("text", ""))
                faves = tweet.get("favorite_count", 0)
                # 重要イベントキーワードの検出
                high_impact_keywords = ["FOMC", "雇用統計", "nonfarm", "CPI", "GDP", "日銀", "BOJ", "利上げ", "利下げ", "rate"]
                impact = "high" if any(kw.lower() in text.lower() for kw in high_impact_keywords) else "medium"
                events.append({
                    "text": text[:200],
                    "faves": faves,
                    "impact": impact,
                    "handle": tweet.get("user", {}).get("screen_name", ""),
                })

        except Exception as e:
            logger.warning("経済カレンダー取得エラー: %s", e)

    events.sort(key=lambda e: e["faves"], reverse=True)
    result = events[:5]
    logger.info("経済イベント取得: %d件", len(result))
    return result


# ============================================================
# Claude API 市場分析
# ============================================================

# プロンプトテンプレート（7鉄則準拠）
SYSTEM_PROMPT = """\
あなたは15年のプロップファーム経験を持つFXアナリストです。
テクニカル指標・市場センチメント・経済イベントを総合的に分析します。

重要な制約:
- 「BUY」「SELL」の直接指示は絶対に出さない。方向感のみ示す
- 高ボラティリティ環境では慎重な判断を推奨
- 確信度0.3未満の場合はneutralを返す
- 予測の精度に過度な自信を持たない（「為替市場は基本的にランダム」という前提）
- 重要経済イベントがある日はconfidenceを下げる（イベント結果は予測不能）
- SNS投稿はナラティブの参考にするが、個別投稿を鵜呑みにしない
- 理由は2-3文で簡潔に

出力は必ず以下のJSON形式のみ。説明文やコードブロックは不要:
{
  "direction": "bullish" | "bearish" | "neutral",
  "confidence": 0.0-1.0,
  "regime": "trending" | "ranging" | "volatile" | "unknown",
  "key_levels": {
    "support": <float>,
    "resistance": <float>
  },
  "reasoning": "<string: 2-3文の分析要旨>",
  "risk_factors": ["<string: リスク要因1>", "<string: リスク要因2>", ...],
  "market_narrative": "<string: 現在市場を支配しているナラティブを1文で>"
}"""

USER_PROMPT_TEMPLATE = """\
以下は{instrument}の直近テクニカル指標サマリーです。
このデータに基づき、現在の市場環境を分析してください。

## H4足（メインタイムフレーム）
- 終値: {last_close}
- RSI(14): {rsi}
- ADX(14): {adx}
- ATR(14): {atr}
- MFI(14): {mfi}
- MA(20): {ma_20} / MA(50): {ma_50}
- MA位置: {ma_position}
- BBW比率: {bbw_ratio}（1.0=平均、低い=スクイーズ）
- レジーム: {regime}

## 日足（上位足コンテキスト）
- D1 RSI: {d1_rsi}
- D1 ADX: {d1_adx}
- D1トレンド: {d1_trend}
{sentiment_section}{calendar_section}
上記を総合的に判断し、方向感・確信度・レジーム・重要水準・リスク要因をJSON形式で回答してください。
逆張りの視点も含め、この分析が間違っている可能性のある理由も risk_factors に含めてください。
market_narrativeには、現在の市場を支配しているストーリー（金利差、地政学リスク、リスクオン/オフ等）を1文で記述してください。"""


def analyze_with_claude(
    indicators: dict,
    sentiment: list[dict] | None = None,
    economic_events: list[dict] | None = None,
) -> dict:
    """
    Claude APIでテクニカル指標+センチメント+経済イベントを分析し、
    市場環境JSONを返す。

    3層入力（FinMem / TradingAgents方式）:
    - テクニカル指標（既存）
    - 市場センチメント（SocialData API: @loopdomナラティブ分析）
    - 経済イベント（SocialData API: マクロ解釈）

    Args:
        indicators: fetch_mt5_data()の返却値
        sentiment: X投稿リスト（市場センチメント）
        economic_events: 経済イベントリスト

    Returns:
        market_analysis.json に書き込む辞書
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEYが設定されていません。.envファイルを確認してください。"
        )

    ind = indicators["indicators"]
    daily = indicators["daily_context"]

    # センチメントセクション構築
    sentiment_section = ""
    if sentiment:
        lines = ["\n## 市場センチメント（X投稿から抽出）"]
        for i, t in enumerate(sentiment[:7], 1):
            lines.append(f"{i}. @{t['handle']}（{t['faves']}いいね）: {t['text'][:150]}")
        sentiment_section = "\n".join(lines) + "\n"

    # 経済カレンダーセクション構築
    calendar_section = ""
    if economic_events:
        lines = ["\n## 本日の経済イベント（注意）"]
        for e in economic_events:
            lines.append(f"- [{e['impact'].upper()}] @{e['handle']}: {e['text'][:120]}")
        calendar_section = "\n".join(lines) + "\n"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        instrument=indicators["instrument"],
        last_close=indicators["last_close"],
        rsi=ind.get("rsi_14", "N/A"),
        adx=ind.get("adx_14", "N/A"),
        atr=ind.get("atr_14", "N/A"),
        mfi=ind.get("mfi_14", "N/A"),
        ma_20=ind.get("ma_20", "N/A"),
        ma_50=ind.get("ma_50", "N/A"),
        ma_position=ind.get("ma_position", "N/A"),
        bbw_ratio=ind.get("bbw_ratio", "N/A"),
        regime=ind.get("regime", "N/A"),
        d1_rsi=daily.get("d1_rsi", "N/A"),
        d1_adx=daily.get("d1_adx", "N/A"),
        d1_trend=daily.get("d1_trend", "N/A"),
        sentiment_section=sentiment_section,
        calendar_section=calendar_section,
    )

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": AI_MODEL_ID,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    logger.info("Claude API呼び出し（モデル: %s）...", AI_MODEL_ID)

    resp = requests.post(
        CLAUDE_API_URL, headers=headers, json=payload, timeout=CLAUDE_API_TIMEOUT
    )
    resp.raise_for_status()

    result = resp.json()
    content = result.get("content", [{}])[0].get("text", "")

    # JSONパース（コードブロック対応）
    json_str = content.strip()
    if json_str.startswith("```"):
        # ```json ... ``` を除去
        lines = json_str.split("\n")
        json_str = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        )

    analysis = json.loads(json_str)

    # タイムスタンプを追加
    analysis["timestamp"] = datetime.now(timezone.utc).isoformat()
    analysis["model"] = AI_MODEL_ID
    analysis["input_indicators"] = indicators

    return analysis


# ============================================================
# Slack レポート投稿（Step 6）
# ============================================================


def post_slack_report(analysis: dict, webhook_url: str) -> bool:
    """
    分析結果を人間が読める形式でSlackに投稿する。

    Args:
        analysis: Claude APIの分析結果
        webhook_url: Slack Incoming Webhook URL

    Returns:
        成功でTrue
    """
    direction_map = {
        "bullish": "やや強気",
        "bearish": "やや弱気",
        "neutral": "中立",
    }
    regime_map = {
        "trending": "トレンド相場",
        "ranging": "レンジ相場",
        "volatile": "高ボラティリティ",
        "unknown": "判定不能",
    }

    direction = analysis.get("direction", "neutral")
    confidence = analysis.get("confidence", 0.0)
    regime = analysis.get("regime", "unknown")
    key_levels = analysis.get("key_levels", {})
    reasoning = analysis.get("reasoning", "")
    risk_factors = analysis.get("risk_factors", [])
    indicators = analysis.get("input_indicators", {})
    ind = indicators.get("indicators", {})

    # 方向に応じた色
    color_map = {"bullish": "#36a64f", "bearish": "#dc3545", "neutral": "#ffc107"}
    color = color_map.get(direction, "#2196F3")

    instrument = indicators.get("instrument", "USD_JPY")
    last_close = indicators.get("last_close", "N/A")

    # リスク要因テキスト
    risk_text = "\n".join(f"- {r}" for r in risk_factors) if risk_factors else "- なし"

    text = (
        f"*{instrument} 日次市場環境レポート*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*方向感*: {direction_map.get(direction, direction)} "
        f"(確信度: {confidence:.2f})\n"
        f"*レジーム*: {regime_map.get(regime, regime)}\n"
        f"*終値*: {last_close}\n"
        f"*ADX*: {ind.get('adx_14', 'N/A')} | "
        f"*RSI*: {ind.get('rsi_14', 'N/A')} | "
        f"*MFI*: {ind.get('mfi_14', 'N/A')}\n"
        f"*サポート*: {key_levels.get('support', 'N/A')} | "
        f"*レジスタンス*: {key_levels.get('resistance', 'N/A')}\n\n"
        f"*分析要旨*:\n> {reasoning}\n\n"
        f"*ナラティブ*: {analysis.get('market_narrative', 'N/A')}\n\n"
        f"*リスク要因*:\n{risk_text}\n\n"
        f"_モデル: {analysis.get('model', 'N/A')} | "
        f"情報源: テクニカル"
        f"{' + センチメント' + str(analysis.get('input_sources', {}).get('sentiment_tweets', 0)) + '件' if analysis.get('input_sources', {}).get('sentiment_tweets') else ''}"
        f"{' + 経済イベント' + str(analysis.get('input_sources', {}).get('economic_events', 0)) + '件' if analysis.get('input_sources', {}).get('economic_events') else ''}"
        f"_"
    )

    payload = {
        "attachments": [
            {
                "color": color,
                "text": text,
                "mrkdwn_in": ["text"],
            }
        ]
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("Slackレポート投稿成功")
            return True
        logger.warning("Slackレポート投稿失敗 (HTTP %d): %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        logger.warning("Slackレポート投稿エラー: %s", e)
        return False


# ============================================================
# メイン
# ============================================================


def main():
    parser = argparse.ArgumentParser(
        description="FX日次AI市場環境分析（MT5→Claude API→JSON+Slack）"
    )
    parser.add_argument(
        "--instrument",
        default=DEFAULT_INSTRUMENT,
        help="分析対象の通貨ペア（デフォルト: USD_JPY）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="MT5/Claude APIを呼ばず、ダミーデータで動作確認",
    )
    parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Slackレポート投稿をスキップ",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_project_root / "data" / "market_analysis.json",
        help="出力先JSONファイルパス",
    )
    args = parser.parse_args()

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("=== 日次AI市場環境分析 開始 ===")
    logger.info("通貨ペア: %s", args.instrument)

    if args.dry_run:
        # ダミーデータで動作確認
        logger.info("ドライラン: ダミーデータを使用")
        analysis = {
            "direction": "bullish",
            "confidence": 0.65,
            "regime": "trending",
            "key_levels": {"support": 149.20, "resistance": 150.80},
            "reasoning": "ドライラン: MA短期が長期を上回り上昇トレンド継続中。ADXが25以上でトレンド強度は十分。",
            "risk_factors": [
                "ドライラン: D1 ADXが弱く上位足でトレンド不明確",
                "ドライラン: 150.80のレジスタンス接近",
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": AI_MODEL_ID,
            "input_indicators": {
                "instrument": args.instrument,
                "timeframe": "H4",
                "last_close": 150.123,
                "indicators": {
                    "rsi_14": 62.3,
                    "adx_14": 28.5,
                    "atr_14": 0.452,
                    "mfi_14": 55.2,
                    "ma_20": 149.823,
                    "ma_50": 149.456,
                    "ma_position": "短期>長期（上昇トレンド示唆）",
                    "bbw_ratio": 1.12,
                    "regime": "trending",
                },
                "daily_context": {
                    "d1_rsi": 58.1,
                    "d1_adx": 22.3,
                    "d1_trend": "横ばい",
                },
            },
        }
    else:
        # MT5データ取得（テクニカル指標）
        logger.info("MT5からデータ取得中...")
        indicators = fetch_mt5_data(args.instrument)
        logger.info("テクニカル指標算出完了")

        # 市場センチメント取得（SocialData API）
        logger.info("市場センチメント取得中...")
        sentiment = fetch_market_sentiment(args.instrument)

        # 経済カレンダー取得（SocialData API）
        logger.info("経済イベント取得中...")
        economic_events = fetch_economic_calendar()

        # Claude API分析（テクニカル+センチメント+経済イベント）
        logger.info("Claude APIで分析中（3層入力: テクニカル+センチメント+マクロ）...")
        analysis = analyze_with_claude(indicators, sentiment, economic_events)

        # 入力ソース情報を記録
        analysis["input_sources"] = {
            "technical": True,
            "sentiment_tweets": len(sentiment),
            "economic_events": len(economic_events),
        }

    # JSON出力
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    logger.info("分析結果を保存: %s", args.output)

    # 結果サマリー
    logger.info(
        "分析結果: direction=%s, confidence=%.2f, regime=%s",
        analysis.get("direction"),
        analysis.get("confidence", 0),
        analysis.get("regime"),
    )

    # Slackレポート投稿
    if not args.no_slack and SLACK_WEBHOOK_URL:
        logger.info("Slackレポート投稿中...")
        post_slack_report(analysis, SLACK_WEBHOOK_URL)
    elif not SLACK_WEBHOOK_URL:
        logger.info("SLACK_WEBHOOK_URL未設定のためSlack投稿スキップ")
    else:
        logger.info("--no-slackオプションによりSlack投稿スキップ")

    logger.info("=== 日次AI市場環境分析 完了 ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("致命的エラー: %s", e)
        sys.exit(1)
