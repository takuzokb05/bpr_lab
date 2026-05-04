"""TradePostMortem の Claude API 呼び出しのテスト

監査5/4: max_tokens=512 では日本語 JSON が確実に切れて
JSONDecodeError("Unterminated string ...") が発生していたバグ修正の回帰防止。
"""
from unittest.mock import MagicMock, patch

from src.trade_postmortem import TradePostMortem


def _mock_response(text: str, stop_reason: str = "end_turn") -> MagicMock:
    """Claude API レスポンスを模擬する。"""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "stop_reason": stop_reason,
        "content": [{"type": "text", "text": text}],
    }
    return resp


def test_call_claude_parses_valid_json():
    """正常な JSON 応答を dict として返す"""
    pm = TradePostMortem(db_path=None)
    valid_json = (
        '{"outcome": "loss", "primary_cause": "RSIが過熱せずエントリーが早すぎ", '
        '"entry_analysis": "x", "exit_analysis": "y", '
        '"parameter_suggestion": {"parameter": null, "current_value": null, '
        '"suggested_value": null, "reasoning": "z"}, '
        '"hindsight_warning": "w"}'
    )
    with patch("src.trade_postmortem.requests.post",
               return_value=_mock_response(valid_json)):
        result = pm._call_claude("test prompt")
    assert result is not None
    assert result["outcome"] == "loss"
    assert result["parameter_suggestion"]["reasoning"] == "z"


def test_call_claude_strips_code_fence():
    """```json ... ``` フェンス付きでも parse できる"""
    pm = TradePostMortem(db_path=None)
    fenced = '```json\n{"outcome": "win"}\n```'
    with patch("src.trade_postmortem.requests.post",
               return_value=_mock_response(fenced)):
        result = pm._call_claude("test")
    assert result == {"outcome": "win"}


def test_call_claude_retries_on_truncation():
    """max_tokens で truncated 検出時、より大きい max_tokens でリトライする"""
    pm = TradePostMortem(db_path=None)
    truncated = '{"outcome": "loss", "primary_cause": "途中で切れ'  # JSON 不完全
    valid = '{"outcome": "loss", "primary_cause": "完全なJSON"}'

    responses = [
        _mock_response(truncated, stop_reason="max_tokens"),
        _mock_response(valid, stop_reason="end_turn"),
    ]
    with patch("src.trade_postmortem.requests.post", side_effect=responses):
        result = pm._call_claude("test")
    assert result == {"outcome": "loss", "primary_cause": "完全なJSON"}


def test_call_claude_no_retry_on_non_truncation_parse_failure():
    """truncation 以外の parse 失敗（モデルが本当に invalid JSON 返した）はリトライしない"""
    pm = TradePostMortem(db_path=None)
    invalid = "this is not JSON at all"
    with patch("src.trade_postmortem.requests.post",
               return_value=_mock_response(invalid, stop_reason="end_turn")) as mock_post:
        result = pm._call_claude("test")
    assert result is None
    assert mock_post.call_count == 1, "invalid JSON でリトライしてはいけない"


def test_call_claude_gives_up_after_one_retry():
    """リトライしても truncated なら諦める（無限リトライ禁止）"""
    pm = TradePostMortem(db_path=None)
    truncated = '{"outcome": "loss", "primary_cause": "切れる'

    responses = [
        _mock_response(truncated, stop_reason="max_tokens"),
        _mock_response(truncated, stop_reason="max_tokens"),
    ]
    with patch("src.trade_postmortem.requests.post", side_effect=responses) as mock_post:
        result = pm._call_claude("test")
    assert result is None
    assert mock_post.call_count == 2, "1 度だけリトライ、それ以上はしない"


def test_max_tokens_initial_is_large_enough():
    """監査回帰防止: 初回 max_tokens が 512 より十分大きい"""
    pm = TradePostMortem(db_path=None)
    assert pm._MAX_TOKENS_INITIAL >= 1024, (
        f"初回 max_tokens={pm._MAX_TOKENS_INITIAL} は小さすぎる。"
        "日本語 JSON で truncation が頻発する"
    )
    assert pm._MAX_TOKENS_RETRY > pm._MAX_TOKENS_INITIAL


def test_call_claude_returns_none_on_request_exception():
    """ネットワークエラーは None を返す（リトライしない）"""
    import requests
    pm = TradePostMortem(db_path=None)
    with patch("src.trade_postmortem.requests.post",
               side_effect=requests.exceptions.ConnectionError("boom")) as mock_post:
        result = pm._call_claude("test")
    assert result is None
    assert mock_post.call_count == 1


def test_call_claude_returns_none_on_timeout():
    """timeout は None を返す（リトライしない）"""
    import requests
    pm = TradePostMortem(db_path=None)
    with patch("src.trade_postmortem.requests.post",
               side_effect=requests.exceptions.Timeout("slow")) as mock_post:
        result = pm._call_claude("test")
    assert result is None
    assert mock_post.call_count == 1
