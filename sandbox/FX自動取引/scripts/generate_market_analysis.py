"""
FX自動取引システム — 日次市場環境分析スクリプト

Windows VPS上でMT5から直接価格データを取得し、
テクニカル指標をルールベースで分析してdata/market_analysis.jsonに書き出す。
センチメントデータ（SocialData API）がある場合のみClaude APIでナラティブ解釈を補完。
オプションでSlack Webhookにレポートを投稿する。

2パス構成:
  Path 1（常時）: ルールベース分析 — MA/RSI/ADX/ATRから方向感・確信度・レジームを判定
  Path 2（条件付き）: LLMセンチメント解釈 — ツイート/経済イベントがある場合のみClaude API

タスクスケジューラで日次実行（JST 6:30）:
  schtasks /Create /TN "FX_MarketAnalysis" ^
    /TR "cmd.exe /c cd /d C:\\bpr_lab\\fx_trading && python scripts/generate_market_analysis.py" ^
    /SC DAILY /ST 06:30 /RL HIGHEST /F
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
    DEFAULT_INSTRUMENTS,
    MA_LONG_PERIOD,
    MA_SHORT_PERIOD,
    MFI_PERIOD,
    RSI_PERIOD,
    SLACK_WEBHOOK_URL,
)

logger = logging.getLogger(__name__)

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
    symbol: str, timeframe_h4: int = 100, timeframe_d1: int = 30,
    _mt5_initialized: bool = False,
) -> dict:
    """
    MT5から価格データを取得してテクニカル指標を計算する。

    Args:
        symbol: 通貨ペア（例: "USD_JPY"）
        timeframe_h4: H4足の取得本数
        timeframe_d1: D1足の取得本数
        _mt5_initialized: True の場合、MT5の初期化/シャットダウンをスキップ
                          （呼び出し元で管理している場合に使用）

    Returns:
        テクニカル指標の辞書
    """
    import MetaTrader5 as mt5

    if not _mt5_initialized:
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
        if not _mt5_initialized:
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


def fetch_news_headlines(max_items: int = 12) -> list[dict]:
    """
    FX関連の主要ニュース見出しを複数RSSから取得する。

    情報源（2026-04検証済、認証不要RSS）:
    - Forexlive (FX特化、25件/取得)
    - FXStreet (FX専門記事)
    - Investing.com Forex/AllFX
    - Google News RSS検索（Reuters/Bloomberg等を間接取得、100件/取得）
    - BBC Business (マクロ補助)

    Reuters直接RSS (feeds.reuters.com) は2020年頃に廃止されたため、
    Google News RSS経由で間接的に取得する。

    Returns:
        [{"title": str, "source": str, "published": str, "link": str}, ...]
    """
    import email.utils as eut
    import xml.etree.ElementTree as ET

    feeds = [
        ("Forexlive", "https://www.forexlive.com/feed"),
        ("FXStreet", "https://www.fxstreet.com/rss/news"),
        ("Investing Forex", "https://www.investing.com/rss/news_1.rss"),
        ("Investing AllFX", "https://www.investing.com/rss/news_285.rss"),
        # Google News RSS: Reuters/Bloomberg等を間接取得
        ("GoogleNews FX",
         "https://news.google.com/rss/search?"
         "q=forex+OR+dollar+OR+yen+OR+euro&hl=en-US&gl=US&ceid=US:en"),
        ("GoogleNews CB",
         "https://news.google.com/rss/search?"
         "q=BOJ+OR+FOMC+OR+ECB+OR+rate+decision&hl=en-US&gl=US&ceid=US:en"),
        ("BBC Business", "http://feeds.bbci.co.uk/news/business/rss.xml"),
    ]

    items: list[dict] = []

    # FX文脈の「強キーワード」（これのいずれかを含むこと）
    strong_keywords = [
        "fx", "forex",
        "fomc", "fed ", "federal reserve", "boj", "ecb", "boe",
        "rate decision", "rate cut", "rate hike", "rate rise",
        "usd/", "eur/", "gbp/", "jpy/", "aud/", "cad/", "chf/", "nzd/",
        "/usd", "/jpy", "/eur", "/gbp",
        "yen", "sterling", "greenback", "euro ",
        "central bank", "monetary policy",
        "cpi", "ppi", "nonfarm", "gdp", "inflation",
        "ドル", "円", "ユーロ", "ポンド", "日銀", "為替",
    ]

    # ノイズ除外（dollar を含む非FX記事を弾く）
    noise_keywords = [
        "dollar general", "dollar tree", "dollar store",
        " ira", "ira ", "roth ira", "brokerage account",
        "art sales", "real estate", "property sale",
        "stock picks", "stocks to buy", "dividend stock",
        "cryptocurrency price", "crypto price",
    ]

    for source, url in feeds:
        try:
            resp = requests.get(
                url,
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (FX-Trading-Bot)"},
            )
            if resp.status_code != 200:
                logger.debug("RSS取得失敗 %s: status=%d", source, resp.status_code)
                continue

            root = ET.fromstring(resp.content)
            # RSS 2.0: channel/item
            entries = root.findall(".//item")
            for entry in entries[:20]:
                title_el = entry.find("title")
                link_el = entry.find("link")
                pub_el = entry.find("pubDate")
                if title_el is None or title_el.text is None:
                    continue
                title = title_el.text.strip()
                lower_title = title.lower()
                # GoogleNewsは検索クエリ自体がFXフィルタなので強キーワード要件を省略。
                # 他feedは強キーワードを1つ以上含むこと（FX文脈確保）。
                if not source.startswith("GoogleNews"):
                    if not any(kw in lower_title for kw in strong_keywords):
                        continue
                # ノイズワードを含んでいたら除外（全feed共通）
                if any(nk in lower_title for nk in noise_keywords):
                    continue

                # Google News RSS はタイトル末尾に " - <媒体名>" が付く。
                # 例: "BOJ likely to hold off raising rates - Reuters"
                # 末尾sourceを抽出して source フィールドに反映、titleからは除去。
                effective_source = source
                if source.startswith("GoogleNews") and " - " in title:
                    body, sep, tail = title.rpartition(" - ")
                    # 媒体名は3-40文字・URL断片でない・キーワード含まない
                    if (3 <= len(tail) <= 40
                            and "http" not in tail
                            and "/" not in tail):
                        effective_source = tail.strip()
                        title = body.strip()

                # 発行時刻を絶対時間に正規化
                pub_str = pub_el.text if pub_el is not None else ""
                try:
                    published = eut.parsedate_to_datetime(pub_str).isoformat()
                except Exception:
                    published = pub_str

                items.append({
                    "title": title[:200],
                    "source": effective_source,
                    "published": published,
                    "link": link_el.text if link_el is not None else "",
                })
        except Exception as e:
            logger.warning("RSS取得エラー %s: %s", source, e)

    # 新しい順、上位max_items件
    items.sort(key=lambda x: x.get("published", ""), reverse=True)
    result = items[:max_items]
    logger.info("ニュース見出し取得: %d件（複数RSSから集約）", len(result))
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

    # VPSロケール非依存にする（UTCで日付確定）
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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
# ルールベース市場分析（LLM不使用、常時実行）
# ============================================================


def analyze_rule_based(indicators: dict) -> dict:
    """
    テクニカル指標からルールベースで市場環境を判定する（LLM不使用）。

    RegimeDetector + ConvictionScorerと同等のロジックを使い、
    テクニカル分類にLLMトークンを消費しない。

    Args:
        indicators: fetch_mt5_data()の返却値

    Returns:
        market_analysis.json互換の辞書
    """
    ind = indicators["indicators"]
    daily = indicators["daily_context"]
    last_close = indicators["last_close"]

    ma_short = ind.get("ma_20")
    ma_long = ind.get("ma_50")
    rsi = ind.get("rsi_14")
    adx = ind.get("adx_14")
    atr = ind.get("atr_14")
    mfi = ind.get("mfi_14")
    bbw_ratio = ind.get("bbw_ratio")
    d1_trend = daily.get("d1_trend", "不明")

    # --- direction判定: MA位置 + RSI + D1トレンドから ---
    direction = "neutral"
    if ma_short is not None and ma_long is not None and rsi is not None:
        if ma_short > ma_long and rsi < 70 and d1_trend != "下降":
            direction = "bullish"
        elif ma_short < ma_long and rsi > 30 and d1_trend != "上昇":
            direction = "bearish"

    # --- confidence算出: ADX強度 + 指標一致度 ---
    if adx is not None:
        confidence = min(adx / 50.0, 1.0)
    else:
        confidence = 0.3

    # ブースト: MAとD1トレンドが一致
    if direction == "bullish" and d1_trend == "上昇":
        confidence += 0.1
    elif direction == "bearish" and d1_trend == "下降":
        confidence += 0.1

    # ペナルティ: RSI極端値
    if rsi is not None and (rsi > 70 or rsi < 30):
        confidence -= 0.2

    # クランプ
    confidence = max(0.1, min(0.9, confidence))

    # --- regime: ADXベース（RegimeDetector同等） ---
    regime = ind.get("regime", "unknown")

    # --- key_levels: ATRベースのサポレジ ---
    if atr is not None:
        support = round(last_close - atr * 2, 5)
        resistance = round(last_close + atr * 2, 5)
    else:
        support = round(last_close * 0.995, 5)
        resistance = round(last_close * 1.005, 5)
    key_levels = {"support": support, "resistance": resistance}

    # --- risk_factors: 矛盾・スクイーズ・中立帯の検出 ---
    risk_factors = []

    # D1とH4のトレンド矛盾
    if direction == "bullish" and d1_trend == "下降":
        risk_factors.append("H4上昇だがD1は下降トレンド — 上位足と矛盾")
    elif direction == "bearish" and d1_trend == "上昇":
        risk_factors.append("H4下降だがD1は上昇トレンド — 上位足と矛盾")

    # BBWスクイーズ警告
    if bbw_ratio is not None and bbw_ratio < 0.7:
        risk_factors.append(f"BBW比率{bbw_ratio:.2f} — ボラティリティ収縮（ブレイクアウト警戒）")

    # MFI中立帯
    if mfi is not None and 40 <= mfi <= 60:
        risk_factors.append(f"MFI{mfi:.1f} — 中立帯で方向性が不明確")

    # RSI極端値
    if rsi is not None:
        if rsi > 70:
            risk_factors.append(f"RSI{rsi:.1f} — 買われすぎ圏で反転リスク")
        elif rsi < 30:
            risk_factors.append(f"RSI{rsi:.1f} — 売られすぎ圏で反転リスク")

    # ADX弱い
    if adx is not None and adx < 20:
        risk_factors.append(f"ADX{adx:.1f} — トレンド不明確でダマシリスク")

    # --- reasoning: テンプレート文生成 ---
    direction_ja = {"bullish": "強気", "bearish": "弱気", "neutral": "中立"}
    regime_ja = {"trending": "トレンド相場", "ranging": "レンジ相場",
                 "transitional": "過渡期", "unknown": "不明"}
    ma_desc = ind.get("ma_position", "")

    reasoning = (
        f"{indicators['instrument']} H4足: {ma_desc}。"
        f" ADX={adx if adx else 'N/A'}で{regime_ja.get(regime, regime)}。"
        f" RSI={rsi if rsi else 'N/A'}、方向感は{direction_ja.get(direction, direction)}。"
    )

    # --- market_narrative ---
    market_narrative = "テクニカル分析のみ（センチメントデータなし）"

    return {
        "direction": direction,
        "confidence": round(confidence, 2),
        "regime": regime,
        "key_levels": key_levels,
        "reasoning": reasoning,
        "risk_factors": risk_factors,
        "market_narrative": market_narrative,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": "rule-based",
        "input_indicators": indicators,
    }


# ============================================================
# LLMセンチメント分析（条件付き — センチメント/イベントがある場合のみ）
# ============================================================

# センチメント解釈に特化したプロンプト（テクニカル分類はルールベースに委任）
SENTIMENT_SYSTEM_PROMPT = """\
あなたはFX市場のセンチメントアナリストです。
SNS投稿と経済イベント情報から、市場ナラティブとリスク要因を解釈します。

重要な制約:
- テクニカル指標の分類（方向感・レジーム等）は行わない — 別途ルールベースで判定済み
- SNS投稿は群衆心理の参考にするが、個別投稿を鵜呑みにしない
- 重要経済イベントがある日はリスク要因として明記
- 理由は簡潔に

出力は必ず以下のJSON形式のみ。説明文やコードブロックは不要:
{
  "sentiment_direction": "bullish" | "bearish" | "neutral",
  "market_narrative": "<string: 市場を支配しているナラティブを1-2文で>",
  "risk_factors": ["<string: センチメント/イベント由来のリスク要因>", ...],
  "sentiment_summary": "<string: センチメントの要約を1文で>"
}"""

SENTIMENT_USER_TEMPLATE = """\
{instrument}について、以下の市場情報からセンチメントを解釈してください。

## テクニカルサマリー（参考）
- 終値: {last_close} / レジーム: {regime} / 方向感(ルール判定): {direction}
{news_section}{sentiment_section}{calendar_section}
市場参加者が何を語り、どんなナラティブが支配的かを分析してください。"""


def analyze_sentiment_with_claude(
    indicators: dict,
    rule_based_direction: str,
    sentiment: list[dict],
    economic_events: list[dict],
    news: list[dict] | None = None,
) -> dict:
    """
    Claude APIでセンチメント+経済イベントのナラティブを解釈する。

    テクニカル分類はルールベースに委任し、LLMはセンチメント解釈に特化。
    トークン消費を削減しつつ、LLMが真に価値を発揮する領域に集中する。

    Args:
        indicators: fetch_mt5_data()の返却値
        rule_based_direction: ルールベースで判定済みの方向感
        sentiment: X投稿リスト（市場センチメント）
        economic_events: 経済イベントリスト

    Returns:
        センチメント分析結果の辞書
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEYが設定されていません。.envファイルを確認してください。"
        )

    # ニュース見出しセクション構築（Reuters/Investing/FXStreet等）
    news_section = ""
    if news:
        lines = ["\n## 主要ニュース見出し（FX関連、24h以内）"]
        for i, n in enumerate(news[:10], 1):
            lines.append(f"{i}. [{n['source']}] {n['title']}")
        news_section = "\n".join(lines) + "\n"

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

    user_prompt = SENTIMENT_USER_TEMPLATE.format(
        instrument=indicators["instrument"],
        last_close=indicators["last_close"],
        regime=indicators["indicators"].get("regime", "unknown"),
        direction=rule_based_direction,
        news_section=news_section,
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
        "max_tokens": 512,  # センチメント解釈のみなので小さめ
        "system": SENTIMENT_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    logger.info("Claude API呼び出し（センチメント解釈、モデル: %s）...", AI_MODEL_ID)

    resp = requests.post(
        CLAUDE_API_URL, headers=headers, json=payload, timeout=CLAUDE_API_TIMEOUT
    )
    resp.raise_for_status()

    result = resp.json()
    content = result.get("content", [{}])[0].get("text", "")

    # JSONパース（コードブロック対応）
    json_str = content.strip()
    if json_str.startswith("```"):
        lines = json_str.split("\n")
        json_str = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        )

    return json.loads(json_str)


# ============================================================
# Slack レポート投稿（Step 6）
# ============================================================


def _format_pair_block(analysis: dict) -> dict:
    """1通貨ペア分のSlack attachmentブロックを生成する。"""
    direction_map = {
        "bullish": "強気",
        "bearish": "弱気",
        "neutral": "中立",
    }
    regime_map = {
        "trending": "トレンド",
        "ranging": "レンジ",
        "volatile": "高ボラ",
        "transitional": "過渡期",
        "unknown": "不明",
    }
    color_map = {"bullish": "#36a64f", "bearish": "#dc3545", "neutral": "#ffc107"}

    direction = analysis.get("direction", "neutral")
    confidence = analysis.get("confidence", 0.0)
    regime = analysis.get("regime", "unknown")
    key_levels = analysis.get("key_levels", {})
    indicators = analysis.get("input_indicators", {})
    ind = indicators.get("indicators", {})
    instrument = indicators.get("instrument", "???")
    last_close = indicators.get("last_close", "N/A")

    # コンパクトな1ペア分テキスト
    text = (
        f"*{instrument}*  {last_close}  "
        f"{direction_map.get(direction, direction)}({confidence:.0%}) "
        f"| {regime_map.get(regime, regime)}\n"
        f"ADX {ind.get('adx_14', '-')} / RSI {ind.get('rsi_14', '-')} / "
        f"MFI {ind.get('mfi_14', '-')}\n"
        f"S: {key_levels.get('support', '-')}  R: {key_levels.get('resistance', '-')}"
    )

    # リスク要因があれば1行追加
    risk_factors = analysis.get("risk_factors", [])
    if risk_factors:
        text += f"\n:warning: {risk_factors[0]}"
        if len(risk_factors) > 1:
            text += f" 他{len(risk_factors)-1}件"

    return {
        "color": color_map.get(direction, "#2196F3"),
        "text": text,
        "mrkdwn_in": ["text"],
    }


def post_slack_report(all_analyses: dict, webhook_url: str) -> bool:
    """
    全ペアの分析結果をまとめてSlackに投稿する。

    Args:
        all_analyses: {"USD_JPY": {...}, "EUR_USD": {...}, ...} 形式
        webhook_url: Slack Incoming Webhook URL

    Returns:
        成功でTrue
    """
    attachments = []
    for instrument in all_analyses:
        analysis = all_analyses[instrument]
        attachments.append(_format_pair_block(analysis))

    # ヘッダー
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    payload = {
        "text": f":chart_with_upwards_trend: *日次市場環境レポート* ({len(all_analyses)}ペア) — {now}",
        "attachments": attachments,
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("Slackレポート投稿成功（%dペア）", len(all_analyses))
            return True
        logger.warning("Slackレポート投稿失敗 (HTTP %d): %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        logger.warning("Slackレポート投稿エラー: %s", e)
        return False


# ============================================================
# メイン
# ============================================================


def _analyze_single_pair(instrument: str, mt5_initialized: bool = False) -> dict:
    """
    1通貨ペア分の分析を実行する（ルールベース + 条件付きLLMセンチメント）。

    Args:
        instrument: 通貨ペア（例: "USD_JPY"）
        mt5_initialized: MT5が初期化済みかどうか

    Returns:
        market_analysis.json互換の分析結果dict
    """
    # MT5データ取得
    logger.info("[%s] MT5からデータ取得中...", instrument)
    indicators = fetch_mt5_data(instrument, _mt5_initialized=mt5_initialized)

    # Path 1: ルールベース分析（常時実行、LLM不使用）
    analysis = analyze_rule_based(indicators)
    logger.info(
        "[%s] ルールベース: direction=%s, confidence=%.2f, regime=%s",
        instrument, analysis["direction"], analysis["confidence"], analysis["regime"],
    )

    # 市場センチメント取得（SocialData API）
    sentiment = fetch_market_sentiment(instrument)

    # 経済カレンダー取得（全ペア共通なので1回だけ取得したいが、現状はペアごと）
    economic_events = fetch_economic_calendar()

    # 一般ニュース見出し取得（Reuters/Investing/FXStreet等のRSS）
    news = fetch_news_headlines()

    # Path 2: LLMセンチメント解釈（ニュース/センチメント/イベントがある場合のみ）
    has_narrative_data = (
        len(sentiment) > 0 or len(economic_events) > 0 or len(news) > 0
    )
    if has_narrative_data:
        logger.info(
            "[%s] LLM統合分析（ニュース%d件、ツイート%d件、イベント%d件）...",
            instrument, len(news), len(sentiment), len(economic_events),
        )
        try:
            llm_result = analyze_sentiment_with_claude(
                indicators, analysis["direction"], sentiment, economic_events,
                news=news,
            )
            analysis["market_narrative"] = llm_result.get(
                "market_narrative", analysis["market_narrative"]
            )
            analysis["risk_factors"].extend(llm_result.get("risk_factors", []))
            if llm_result.get("sentiment_direction") == analysis["direction"]:
                analysis["confidence"] = min(analysis["confidence"] + 0.1, 0.9)
            analysis["model"] = f"rule-based+{AI_MODEL_ID}"
        except Exception as e:
            logger.warning("[%s] LLM統合分析失敗（ルールベース結果を維持）: %s", instrument, e)
    else:
        logger.info("[%s] ナラティブデータなし - ルールベースのみ", instrument)

    # 入力ソース情報を記録
    analysis["input_sources"] = {
        "technical": True,
        "news_items": len(news),
        "sentiment_tweets": len(sentiment),
        "economic_events": len(economic_events),
        "llm_used": has_narrative_data,
    }

    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="FX日次市場環境分析（MT5→ルールベース分析[+LLMセンチメント]→JSON+Slack）"
    )
    parser.add_argument(
        "--instruments", nargs="+", default=None,
        help="分析対象の通貨ペア（複数指定可、デフォルト: DEFAULT_INSTRUMENTS）",
    )
    parser.add_argument(
        "--instrument", default=None,
        help="分析対象の通貨ペア（単一指定、後方互換用）",
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

    # 通貨ペアリスト解決（--instrument単一指定 > --instruments複数指定 > デフォルト）
    if args.instrument:
        instruments = [args.instrument]
    elif args.instruments:
        instruments = args.instruments
    else:
        instruments = DEFAULT_INSTRUMENTS

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("=== 日次市場環境分析 開始（%dペア） ===", len(instruments))
    logger.info("通貨ペア: %s", instruments)

    # 全ペアの分析結果を格納（ペア名 → 分析dict）
    all_analyses: dict[str, dict] = {}

    if args.dry_run:
        logger.info("ドライラン: ダミーデータを使用")
        for instrument in instruments:
            dummy_indicators = {
                "instrument": instrument,
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
            }
            all_analyses[instrument] = analyze_rule_based(dummy_indicators)
    else:
        # MT5を1回だけ初期化して全ペアを処理
        import MetaTrader5 as mt5
        if not mt5.initialize():
            raise RuntimeError(f"MT5初期化失敗: {mt5.last_error()}")
        try:
            for instrument in instruments:
                try:
                    analysis = _analyze_single_pair(instrument, mt5_initialized=True)
                    all_analyses[instrument] = analysis
                except Exception as e:
                    logger.error("[%s] 分析失敗（スキップ）: %s", instrument, e)
        finally:
            mt5.shutdown()

    # JSON出力（ペア名キーのdict形式）
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_analyses, f, ensure_ascii=False, indent=2)
    logger.info("分析結果を保存: %s（%dペア）", args.output, len(all_analyses))

    # 結果サマリー
    for instrument, analysis in all_analyses.items():
        logger.info(
            "  %s: direction=%s, confidence=%.2f, regime=%s",
            instrument,
            analysis.get("direction"),
            analysis.get("confidence", 0),
            analysis.get("regime"),
        )

    # Slackレポート投稿
    if not args.no_slack and SLACK_WEBHOOK_URL:
        logger.info("Slackレポート投稿中...")
        post_slack_report(all_analyses, SLACK_WEBHOOK_URL)
    elif not SLACK_WEBHOOK_URL:
        logger.info("SLACK_WEBHOOK_URL未設定のためSlack投稿スキップ")
    else:
        logger.info("--no-slackオプションによりSlack投稿スキップ")

    logger.info("=== 日次市場環境分析 完了（%dペア） ===", len(all_analyses))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("致命的エラー: %s", e)
        sys.exit(1)
