"""
T4: pair_config.py のユニットテスト

YAMLローダー、フォールバック、欠けキー補完、キャッシュリロードを検証する。
"""

from pathlib import Path

import pytest

from src import config as global_config
from src import pair_config as pc
from src.pair_config import (
    DEFAULT_PAIR_CONFIG_PATH,
    get_allowed_sessions,
    get_pair_config,
    reload_pair_config,
)


@pytest.fixture(autouse=True)
def reset_cache_after_test():
    """各テスト後にキャッシュをデフォルトに戻す"""
    yield
    reload_pair_config()


@pytest.fixture
def yaml_path(tmp_path: Path):
    """テスト用YAMLパスを返すヘルパー"""

    def _write(content: str) -> Path:
        path = tmp_path / "pair_config.yaml"
        path.write_text(content, encoding="utf-8")
        reload_pair_config(path)
        return path

    return _write


class TestGetPairConfig:
    """get_pair_config の振る舞い"""

    def test_returns_yaml_values_for_defined_pair(self, yaml_path):
        yaml_path(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
            "  rsi_oversold: 25\n"
            "  rsi_overbought: 75\n"
            "  adx_threshold: 30\n"
            "  atr_sl_mult: 1.8\n"
            "  atr_tp1_mult: 1.2\n"
            "  atr_tp2_mult: 3.5\n"
        )
        cfg = get_pair_config("EUR_USD")
        assert cfg["rsi_oversold"] == 25
        assert cfg["rsi_overbought"] == 75
        assert cfg["adx_threshold"] == 30
        assert cfg["atr_sl_mult"] == 1.8
        assert cfg["atr_tp1_mult"] == 1.2
        assert cfg["atr_tp2_mult"] == 3.5
        assert cfg["allowed_sessions"][0]["label"] == "LDN-NY"

    def test_falls_back_to_global_for_undefined_pair(self, yaml_path):
        yaml_path(
            "EUR_USD:\n"
            "  allowed_sessions: []\n"
        )
        cfg = get_pair_config("UNKNOWN_PAIR")
        # グローバル設定値にフォールバック
        assert cfg["rsi_oversold"] == global_config.RSI_OVERSOLD
        assert cfg["rsi_overbought"] == global_config.RSI_OVERBOUGHT
        assert cfg["adx_threshold"] == global_config.ADX_THRESHOLD
        assert cfg["atr_sl_mult"] == global_config.ATR_MULTIPLIER
        # 未定義ペアの allowed_sessions は空（24時間扱い）
        assert cfg["allowed_sessions"] == []

    def test_partial_override_fills_missing_keys(self, yaml_path):
        # rsi_oversold だけ定義、他はフォールバック
        yaml_path(
            "EUR_USD:\n"
            "  rsi_oversold: 20\n"
        )
        cfg = get_pair_config("EUR_USD")
        assert cfg["rsi_oversold"] == 20
        assert cfg["rsi_overbought"] == global_config.RSI_OVERBOUGHT
        assert cfg["adx_threshold"] == global_config.ADX_THRESHOLD

    def test_yaml_missing_uses_global_defaults(self, tmp_path):
        # 存在しないパス → 警告ログ + 空dict扱い → 全ペアでフォールバック
        nonexistent = tmp_path / "does_not_exist.yaml"
        reload_pair_config(nonexistent)
        cfg = get_pair_config("EUR_USD")
        assert cfg["rsi_oversold"] == global_config.RSI_OVERSOLD
        assert cfg["allowed_sessions"] == []

    def test_malformed_yaml_falls_back(self, tmp_path):
        # パースエラー → 全ペアフォールバック
        path = tmp_path / "bad.yaml"
        path.write_text("EUR_USD:\n  rsi: [unclosed\n", encoding="utf-8")
        reload_pair_config(path)
        cfg = get_pair_config("EUR_USD")
        assert cfg["rsi_oversold"] == global_config.RSI_OVERSOLD

    def test_yaml_top_level_not_dict_falls_back(self, tmp_path):
        path = tmp_path / "list.yaml"
        path.write_text("- item1\n- item2\n", encoding="utf-8")
        reload_pair_config(path)
        cfg = get_pair_config("EUR_USD")
        assert cfg["rsi_oversold"] == global_config.RSI_OVERSOLD

    def test_empty_yaml_falls_back(self, tmp_path):
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        reload_pair_config(path)
        cfg = get_pair_config("EUR_USD")
        assert cfg["rsi_oversold"] == global_config.RSI_OVERSOLD


class TestGetAllowedSessions:
    """get_allowed_sessions ショートカット"""

    def test_returns_list(self, yaml_path):
        yaml_path(
            "EUR_USD:\n"
            "  allowed_sessions:\n"
            "    - {start: \"21:00\", end: \"02:00\", label: \"LDN-NY\"}\n"
            "    - {start: \"09:00\", end: \"15:00\", label: \"Tokyo\"}\n"
        )
        sessions = get_allowed_sessions("EUR_USD")
        assert len(sessions) == 2
        assert sessions[0]["label"] == "LDN-NY"

    def test_undefined_pair_returns_empty(self, yaml_path):
        yaml_path("EUR_USD:\n  rsi_oversold: 30\n")
        sessions = get_allowed_sessions("UNKNOWN")
        assert sessions == []

    def test_invalid_sessions_type_returns_empty(self, yaml_path):
        # allowed_sessions が文字列など不正型 → 空リスト
        yaml_path(
            "EUR_USD:\n"
            "  allowed_sessions: \"not a list\"\n"
        )
        sessions = get_allowed_sessions("EUR_USD")
        assert sessions == []


class TestReloadCache:
    """キャッシュとリロードのテスト"""

    def test_reload_picks_up_changes(self, tmp_path):
        path = tmp_path / "pair_config.yaml"
        path.write_text(
            "EUR_USD:\n  rsi_oversold: 25\n", encoding="utf-8",
        )
        reload_pair_config(path)
        assert get_pair_config("EUR_USD")["rsi_oversold"] == 25

        # ファイル更新 → リロード
        path.write_text(
            "EUR_USD:\n  rsi_oversold: 20\n", encoding="utf-8",
        )
        reload_pair_config(path)
        assert get_pair_config("EUR_USD")["rsi_oversold"] == 20

    def test_different_path_triggers_reload(self, tmp_path):
        path1 = tmp_path / "a.yaml"
        path1.write_text("EUR_USD:\n  rsi_oversold: 25\n", encoding="utf-8")
        path2 = tmp_path / "b.yaml"
        path2.write_text("EUR_USD:\n  rsi_oversold: 20\n", encoding="utf-8")

        assert get_pair_config("EUR_USD", path=path1)["rsi_oversold"] == 25
        # 異なるパスを渡すと自動的にリロード
        assert get_pair_config("EUR_USD", path=path2)["rsi_oversold"] == 20


class TestRealYAMLFile:
    """リポジトリ同梱の config/pair_config.yaml が読み込めること"""

    def test_default_yaml_loads_for_all_pairs(self):
        reload_pair_config()  # デフォルトパス
        for pair in ("EUR_USD", "USD_JPY", "GBP_JPY", "AUD_USD",
                     "GBP_USD", "EUR_JPY"):
            cfg = get_pair_config(pair)
            assert isinstance(cfg["allowed_sessions"], list)
            assert len(cfg["allowed_sessions"]) >= 1
            assert "rsi_oversold" in cfg
            assert "atr_sl_mult" in cfg

    def test_default_yaml_path_exists(self):
        # PR時のスモーク
        assert DEFAULT_PAIR_CONFIG_PATH.exists(), (
            f"pair_config.yaml が見つかりません: {DEFAULT_PAIR_CONFIG_PATH}"
        )
