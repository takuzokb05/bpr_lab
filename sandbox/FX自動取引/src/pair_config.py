"""
ペア別パラメータ設定ローダー（T4）

config/pair_config.yaml から通貨ペア毎の設定を読み込み、
グローバル設定（src.config）をオーバーライドできるインターフェイスを提供する。

設計方針:
- YAML不在時は src.config のグローバル値にフォールバックする（後方互換）
- 同一プロセス内で複数回 get_pair_config() が呼ばれる場合に備えてキャッシュ
- ホットリロード（テスト・運用時の手動更新）用に reload_pair_config() を提供
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from src import config as global_config

logger = logging.getLogger(__name__)

# プロジェクトルート / config / pair_config.yaml
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PAIR_CONFIG_PATH = _PROJECT_ROOT / "config" / "pair_config.yaml"

# キャッシュ。初回 get_pair_config() で読み込まれる
_pair_config_cache: Optional[dict[str, dict[str, Any]]] = None
_loaded_path: Optional[Path] = None


def _build_default_pair_config() -> dict[str, Any]:
    """YAML不在時のフォールバック値（src.config のグローバル値）"""
    return {
        "allowed_sessions": [],  # 空 = 24時間許可
        "rsi_oversold": global_config.RSI_OVERSOLD,
        "rsi_overbought": global_config.RSI_OVERBOUGHT,
        "adx_threshold": global_config.ADX_THRESHOLD,
        "atr_sl_mult": global_config.ATR_MULTIPLIER,
        "atr_tp1_mult": 1.0,
        "atr_tp2_mult": global_config.ATR_MULTIPLIER * 1.5,
    }


def _load_yaml(path: Path) -> dict[str, dict[str, Any]]:
    """
    YAMLファイルを読み込んで dict を返す。

    ファイル不在 / パースエラー時は空 dict を返し、警告ログを出す。
    """
    if not path.exists():
        logger.warning(
            "pair_config.yaml が見つかりません（path=%s）。"
            "全ペアでグローバル設定にフォールバックします。",
            path,
        )
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(
            "pair_config.yaml のパースに失敗しました（path=%s）: %s。"
            "全ペアでグローバル設定にフォールバックします。",
            path, e,
        )
        return {}

    if not isinstance(data, dict):
        logger.error(
            "pair_config.yaml のトップレベルは dict である必要があります（path=%s）。"
            "実際の型: %s。フォールバックします。",
            path, type(data).__name__,
        )
        return {}

    return data


def _ensure_loaded(path: Optional[Path] = None) -> None:
    """
    初回呼び出し時、または明示的にパスを指定された場合に読み込みを実行する。

    - path=None: キャッシュ未初期化なら DEFAULT_PAIR_CONFIG_PATH から読み込む。
                 既にロード済みなら何もしない（キャッシュを尊重）。
    - path=指定: 現在のロード元と異なれば再ロードする（テスト用）。
    """
    global _pair_config_cache, _loaded_path
    if path is not None:
        if _pair_config_cache is None or _loaded_path != path:
            _pair_config_cache = _load_yaml(path)
            _loaded_path = path
        return
    if _pair_config_cache is None:
        _pair_config_cache = _load_yaml(DEFAULT_PAIR_CONFIG_PATH)
        _loaded_path = DEFAULT_PAIR_CONFIG_PATH


def reload_pair_config(path: Optional[Path] = None) -> None:
    """
    キャッシュを破棄して再読み込みする。

    テスト時に異なる YAML を読ませる場合や、運用中の手動更新に使用。
    """
    global _pair_config_cache, _loaded_path
    _pair_config_cache = None
    _loaded_path = None
    _ensure_loaded(path)


def get_pair_config(instrument: str, path: Optional[Path] = None) -> dict[str, Any]:
    """
    指定通貨ペアの設定を取得する。

    YAMLに該当ペアの定義がない場合はグローバル設定にフォールバックする。
    YAMLに定義はあるが一部のキーが欠けている場合は、欠けたキーだけフォールバック。

    Args:
        instrument: 通貨ペア（例: "EUR_USD"）
        path: 明示指定する場合のYAMLパス（テスト用）

    Returns:
        ペア設定 dict。キー: allowed_sessions, rsi_oversold, rsi_overbought,
        adx_threshold, atr_sl_mult, atr_tp1_mult, atr_tp2_mult
    """
    _ensure_loaded(path)
    assert _pair_config_cache is not None  # _ensure_loaded で必ず初期化される

    defaults = _build_default_pair_config()
    pair_data = _pair_config_cache.get(instrument)

    if pair_data is None:
        logger.debug(
            "%s の pair_config 定義なし。グローバル設定にフォールバック。",
            instrument,
        )
        return defaults

    # 欠けたキーをデフォルトで補完
    merged = {**defaults, **pair_data}
    return merged


def get_allowed_sessions(
    instrument: str, path: Optional[Path] = None
) -> list[dict[str, str]]:
    """
    指定通貨ペアの許可時間帯リストを取得するショートカット。

    Returns:
        [{"start": "21:00", "end": "02:00", "label": "LDN-NY"}, ...]
        空リストなら24時間許可とみなす。
    """
    cfg = get_pair_config(instrument, path)
    sessions = cfg.get("allowed_sessions", [])
    if not isinstance(sessions, list):
        logger.warning(
            "%s の allowed_sessions が list ではありません（型=%s）。空扱いにします。",
            instrument, type(sessions).__name__,
        )
        return []
    return sessions
