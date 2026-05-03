"""
時間帯フィルター（T4）

JST時刻での取引許可時間帯判定。pair_config.yaml の allowed_sessions に
基づいて、現在時刻が取引可能なセッションに含まれるかを判定する。

設計方針:
- JST (UTC+9) を内部基準とする。MT5/UTC時刻からの変換ヘルパも提供
- 跨日時間帯（例: 21:00-02:00）を境界値含めて正しく判定
  - 包含判定は [start, end) 半開区間（end ちょうどは外）
  - 跨日: start <= now OR now < end
  - 同日: start <= now < end
- allowed_sessions が空 → 24時間許可（後方互換）
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from src.pair_config import get_allowed_sessions

logger = logging.getLogger(__name__)

# JST タイムゾーン
JST = timezone(timedelta(hours=9))


class SessionFilterError(Exception):
    """時間帯フィルター固有のエラー"""


def _parse_hhmm(value: str) -> time:
    """
    "HH:MM" 文字列を datetime.time に変換する。

    Raises:
        SessionFilterError: フォーマット不正、範囲外（24:00 等）
    """
    try:
        hh_str, mm_str = value.split(":", 1)
        hh = int(hh_str)
        mm = int(mm_str)
    except (ValueError, AttributeError) as e:
        raise SessionFilterError(
            f"時刻フォーマットが不正です（HH:MM 期待、実際: {value!r}）: {e}"
        ) from e

    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise SessionFilterError(
            f"時刻範囲が不正です（HH=0-23, MM=0-59、実際: {value!r}）"
        )

    return time(hour=hh, minute=mm)


def to_jst(dt: datetime) -> datetime:
    """
    任意の datetime を JST に変換する。

    naive な datetime は UTC とみなす（MT5 サーバ時刻は通常 UTC）。
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST)


def now_jst() -> datetime:
    """現在のJST時刻を返す。"""
    return datetime.now(tz=JST)


def is_time_in_session(
    now_time: time, start: time, end: time
) -> bool:
    """
    時刻 now_time がセッション [start, end) に含まれるか判定する。

    跨日対応:
    - start < end（同日内、例: 09:00-15:00）: start <= now < end
    - start > end（跨日、例: 21:00-02:00）: start <= now OR now < end
    - start == end: 常に False（0分セッションは無効扱い）

    境界値:
    - start ちょうどは含む（21:00 → True）
    - end ちょうどは含まない（02:00 → False）
    """
    if start == end:
        # 0分セッションは無効
        return False
    if start < end:
        # 同日内
        return start <= now_time < end
    # 跨日
    return now_time >= start or now_time < end


def is_in_allowed_session(
    instrument: str,
    now: Optional[datetime] = None,
) -> bool:
    """
    現在時刻が指定通貨ペアの許可セッションに含まれるかを判定する。

    Args:
        instrument: 通貨ペア（例: "EUR_USD"）
        now: 判定対象の datetime。None なら現在のJST時刻を使用。
             tz-naive な場合は UTC とみなして JST に変換する。

    Returns:
        True: 取引許可時間帯
        False: 取引非許可時間帯（シグナルをスキップすべき）

    Notes:
        allowed_sessions が空（YAML未定義 / 空リスト）→ 24時間許可（True）
    """
    sessions = get_allowed_sessions(instrument)
    if not sessions:
        # 定義なしは24時間許可（後方互換）
        return True

    now_dt = now_jst() if now is None else to_jst(now)
    now_t = now_dt.time()

    for sess in sessions:
        if not isinstance(sess, dict):
            logger.warning(
                "%s の allowed_sessions エントリが dict ではありません（実際: %s）。スキップ。",
                instrument, type(sess).__name__,
            )
            continue

        start_str = sess.get("start")
        end_str = sess.get("end")
        label = sess.get("label", "unnamed")

        if start_str is None or end_str is None:
            logger.warning(
                "%s session %s: start/end が欠けています。スキップ。",
                instrument, label,
            )
            continue

        try:
            start_t = _parse_hhmm(start_str)
            end_t = _parse_hhmm(end_str)
        except SessionFilterError as e:
            logger.warning(
                "%s session %s: パース失敗 — %s。スキップ。",
                instrument, label, e,
            )
            continue

        if is_time_in_session(now_t, start_t, end_t):
            return True

    return False


def get_active_session_label(
    instrument: str,
    now: Optional[datetime] = None,
) -> Optional[str]:
    """
    現在アクティブなセッションのラベルを返す（ログ用）。

    Returns:
        マッチしたセッションの label、マッチなしなら None
    """
    sessions = get_allowed_sessions(instrument)
    if not sessions:
        return "ALL_DAY"

    now_dt = now_jst() if now is None else to_jst(now)
    now_t = now_dt.time()

    for sess in sessions:
        if not isinstance(sess, dict):
            continue
        start_str = sess.get("start")
        end_str = sess.get("end")
        if start_str is None or end_str is None:
            continue
        try:
            start_t = _parse_hhmm(start_str)
            end_t = _parse_hhmm(end_str)
        except SessionFilterError:
            continue
        if is_time_in_session(now_t, start_t, end_t):
            return sess.get("label", "unnamed")

    return None
