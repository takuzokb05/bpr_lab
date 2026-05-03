"""
T4: session_filter.py のユニットテスト

時間帯判定ロジック（境界値、跨日、TZ変換、フォールバック）を検証する。
"""

from datetime import datetime, time, timedelta, timezone
from pathlib import Path

import pytest

from src import session_filter
from src.session_filter import (
    JST,
    SessionFilterError,
    _parse_hhmm,
    get_active_session_label,
    is_in_allowed_session,
    is_time_in_session,
    now_jst,
    to_jst,
)


# ============================================================
# _parse_hhmm
# ============================================================


class TestParseHHMM:
    """HH:MM パースのテスト"""

    def test_parse_valid_basic(self):
        assert _parse_hhmm("09:30") == time(9, 30)

    def test_parse_valid_zero(self):
        assert _parse_hhmm("00:00") == time(0, 0)

    def test_parse_valid_max(self):
        assert _parse_hhmm("23:59") == time(23, 59)

    def test_parse_invalid_format_no_colon(self):
        with pytest.raises(SessionFilterError):
            _parse_hhmm("0930")

    def test_parse_invalid_hour_24(self):
        with pytest.raises(SessionFilterError):
            _parse_hhmm("24:00")

    def test_parse_invalid_minute_60(self):
        with pytest.raises(SessionFilterError):
            _parse_hhmm("12:60")

    def test_parse_invalid_negative(self):
        with pytest.raises(SessionFilterError):
            _parse_hhmm("-1:00")

    def test_parse_invalid_non_numeric(self):
        with pytest.raises(SessionFilterError):
            _parse_hhmm("ab:cd")


# ============================================================
# is_time_in_session（同日内・跨日・境界値）
# ============================================================


class TestIsTimeInSessionSameDay:
    """同日内セッション [start, end) の判定"""

    def test_inside(self):
        # 09:00-15:00 → 12:00 は内側
        assert is_time_in_session(time(12, 0), time(9, 0), time(15, 0)) is True

    def test_start_boundary_included(self):
        # start ちょうどは含む（[start, end)）
        assert is_time_in_session(time(9, 0), time(9, 0), time(15, 0)) is True

    def test_end_boundary_excluded(self):
        # end ちょうどは含まない
        assert is_time_in_session(time(15, 0), time(9, 0), time(15, 0)) is False

    def test_just_before_end(self):
        assert is_time_in_session(time(14, 59), time(9, 0), time(15, 0)) is True

    def test_just_before_start(self):
        assert is_time_in_session(time(8, 59), time(9, 0), time(15, 0)) is False

    def test_outside_after(self):
        assert is_time_in_session(time(16, 0), time(9, 0), time(15, 0)) is False

    def test_outside_before(self):
        assert is_time_in_session(time(7, 0), time(9, 0), time(15, 0)) is False


class TestIsTimeInSessionCrossDay:
    """跨日セッション（start > end）の判定 — 例: 21:00-02:00"""

    def test_inside_after_start(self):
        # 21:00-02:00 → 22:00 は内側
        assert is_time_in_session(time(22, 0), time(21, 0), time(2, 0)) is True

    def test_inside_before_end(self):
        # 21:00-02:00 → 01:00 は内側（翌日の意味）
        assert is_time_in_session(time(1, 0), time(21, 0), time(2, 0)) is True

    def test_start_boundary_included(self):
        # 21:00 ちょうどは含む
        assert is_time_in_session(time(21, 0), time(21, 0), time(2, 0)) is True

    def test_end_boundary_excluded(self):
        # 02:00 ちょうどは含まない
        assert is_time_in_session(time(2, 0), time(21, 0), time(2, 0)) is False

    def test_just_before_start(self):
        # 20:59 は外
        assert is_time_in_session(time(20, 59), time(21, 0), time(2, 0)) is False

    def test_just_after_end(self):
        # 02:01 は外
        assert is_time_in_session(time(2, 1), time(21, 0), time(2, 0)) is False

    def test_outside_midday(self):
        # 12:00 は外
        assert is_time_in_session(time(12, 0), time(21, 0), time(2, 0)) is False

    def test_just_before_end_minute(self):
        # 01:59 は内側
        assert is_time_in_session(time(1, 59), time(21, 0), time(2, 0)) is True


class TestIsTimeInSessionEdgeCases:
    """エッジケース: 0分セッション・end=00:00 等"""

    def test_zero_duration_session(self):
        # start == end → 常に False
        assert is_time_in_session(time(10, 0), time(10, 0), time(10, 0)) is False
        assert is_time_in_session(time(0, 0), time(10, 0), time(10, 0)) is False

    def test_end_at_midnight_cross_day(self):
        # 22:00-00:00 は跨日扱い（end < start）→ 22:00, 23:59 は内、00:00 は外
        assert is_time_in_session(time(23, 0), time(22, 0), time(0, 0)) is True
        assert is_time_in_session(time(0, 0), time(22, 0), time(0, 0)) is False


# ============================================================
# to_jst
# ============================================================


class TestToJST:
    """タイムゾーン変換のテスト"""

    def test_naive_treated_as_utc(self):
        # naive → UTC とみなして JST に変換
        dt = datetime(2026, 5, 3, 12, 0, 0)  # naive
        jst = to_jst(dt)
        assert jst.tzinfo == JST
        assert jst.hour == 21  # UTC 12:00 → JST 21:00

    def test_utc_aware(self):
        dt = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        jst = to_jst(dt)
        assert jst.hour == 21

    def test_already_jst(self):
        dt = datetime(2026, 5, 3, 21, 0, 0, tzinfo=JST)
        jst = to_jst(dt)
        assert jst.hour == 21

    def test_other_tz(self):
        # NY時刻（UTC-5）の08:00 → UTC 13:00 → JST 22:00
        ny = timezone(timedelta(hours=-5))
        dt = datetime(2026, 5, 3, 8, 0, 0, tzinfo=ny)
        jst = to_jst(dt)
        assert jst.hour == 22


class TestNowJST:
    """now_jst のスモークテスト"""

    def test_returns_jst_aware(self):
        n = now_jst()
        assert n.tzinfo == JST


# ============================================================
# is_in_allowed_session（YAML経由の統合）
# ============================================================


@pytest.fixture
def isolated_yaml(tmp_path: Path):
    """テスト用YAMLを書いて pair_config キャッシュをそこに向ける"""
    from src import pair_config as pc

    def _write(content: str) -> Path:
        path = tmp_path / "pair_config.yaml"
        path.write_text(content, encoding="utf-8")
        pc.reload_pair_config(path)
        return path

    yield _write

    # クリーンアップ: デフォルトに戻す
    pc.reload_pair_config()


class TestIsInAllowedSession:
    """pair_config 経由の許可時間帯判定"""

    def test_inside_single_session(self, isolated_yaml):
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        # JST 22:00
        now = datetime(2026, 5, 3, 22, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is True

    def test_outside_single_session(self, isolated_yaml):
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        now = datetime(2026, 5, 3, 12, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is False

    def test_boundary_start_inclusive(self, isolated_yaml):
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        # 20:59 → False
        now = datetime(2026, 5, 3, 20, 59, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is False
        # 21:00 → True
        now = datetime(2026, 5, 3, 21, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is True

    def test_boundary_end_exclusive(self, isolated_yaml):
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        # 01:59 → True
        now = datetime(2026, 5, 4, 1, 59, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is True
        # 02:00 → False
        now = datetime(2026, 5, 4, 2, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is False
        # 02:01 → False
        now = datetime(2026, 5, 4, 2, 1, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is False

    def test_multiple_sessions_match_first(self, isolated_yaml):
        isolated_yaml(
            "USD_JPY:\n"
            "  allowed_sessions:\n"
            "    - {start: \"09:00\", end: \"11:00\", label: \"Tokyo-AM\"}\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        now = datetime(2026, 5, 3, 10, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("USD_JPY", now=now) is True

    def test_multiple_sessions_match_second(self, isolated_yaml):
        isolated_yaml(
            "USD_JPY:\n"
            "  allowed_sessions:\n"
            "    - {start: \"09:00\", end: \"11:00\", label: \"Tokyo-AM\"}\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        now = datetime(2026, 5, 3, 22, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("USD_JPY", now=now) is True

    def test_multiple_sessions_gap(self, isolated_yaml):
        # 11:00-21:00 のギャップは除外
        isolated_yaml(
            "USD_JPY:\n"
            "  allowed_sessions:\n"
            "    - {start: \"09:00\", end: \"11:00\", label: \"Tokyo-AM\"}\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        now = datetime(2026, 5, 3, 15, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("USD_JPY", now=now) is False

    def test_unknown_pair_falls_back_to_24h(self, isolated_yaml):
        # YAMLに定義のないペアは24時間許可（後方互換）
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        now = datetime(2026, 5, 3, 3, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("UNKNOWN_PAIR", now=now) is True

    def test_empty_sessions_list_means_all_day(self, isolated_yaml):
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions: []\n"
        )
        now = datetime(2026, 5, 3, 3, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is True

    def test_utc_input_converted_to_jst(self, isolated_yaml):
        # UTC 13:00 = JST 22:00 → LDN-NY セッション内
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        utc_now = datetime(2026, 5, 3, 13, 0, 0, tzinfo=timezone.utc)
        assert is_in_allowed_session("EUR_USD", now=utc_now) is True

    def test_naive_treated_as_utc(self, isolated_yaml):
        # naive 13:00 → UTC とみなされ JST 22:00
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        naive = datetime(2026, 5, 3, 13, 0, 0)
        assert is_in_allowed_session("EUR_USD", now=naive) is True

    def test_malformed_session_entry_skipped(self, isolated_yaml):
        # start欠けの不正エントリは無視され、もう一方が評価される
        isolated_yaml(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {end: \"02:00\", label: \"broken\"}\n"
            "    - {start: \"09:00\", end: \"15:00\", label: \"valid\"}\n"
        )
        now = datetime(2026, 5, 3, 12, 0, 0, tzinfo=JST)
        assert is_in_allowed_session("EUR_USD", now=now) is True


class TestGetActiveSessionLabel:
    """アクティブセッションラベル取得"""

    def test_returns_matching_label(self, isolated_yaml):
        isolated_yaml(
            "USD_JPY:\n"
            "  allowed_sessions:\n"
            "    - {start: \"09:00\", end: \"11:00\", label: \"Tokyo-AM\"}\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
        )
        now = datetime(2026, 5, 3, 22, 0, 0, tzinfo=JST)
        assert get_active_session_label("USD_JPY", now=now) == "LDN-NY"

    def test_returns_none_when_outside(self, isolated_yaml):
        isolated_yaml(
            "USD_JPY:\n"
            "  allowed_sessions:\n"
            "    - {start: \"09:00\", end: \"11:00\", label: \"Tokyo-AM\"}\n"
        )
        now = datetime(2026, 5, 3, 15, 0, 0, tzinfo=JST)
        assert get_active_session_label("USD_JPY", now=now) is None

    def test_unknown_pair_returns_all_day(self, isolated_yaml):
        isolated_yaml("EUR_USD: {}\n")
        now = datetime(2026, 5, 3, 12, 0, 0, tzinfo=JST)
        assert get_active_session_label("UNKNOWN", now=now) == "ALL_DAY"
