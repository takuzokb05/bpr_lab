"""
T1: main.py の setup_logging のユニットテスト

RotatingFileHandler のローテ事故（5/1 16:06 trading.log 0バイト化）を受けて
TimedRotatingFileHandler に切り替えた際の回帰テスト。
"""
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pytest

# main.py をプロジェクトルートからimport
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import main as main_module  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_root_logger(monkeypatch):
    """各テストでrootロガーを一時クリアし、終了時に復元する。

    pytest の logging プラグインが LogCaptureHandler を root に常駐させるため、
    そのままでは logging.basicConfig が no-op になり setup_logging の効果が確認できない。
    テスト中だけ root.handlers を空にする。
    """
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    # pytestのキャプチャhandler等を一時退避
    root.handlers = []
    yield
    # 後始末: テストで追加したhandlerを閉じてから元に戻す
    for h in list(root.handlers):
        try:
            h.close()
        except Exception:
            pass
    root.handlers = saved_handlers
    root.setLevel(saved_level)


def test_setup_logging_uses_timed_rotating_handler(tmp_path):
    """setup_logging() は TimedRotatingFileHandler を取り付ける（RotatingFileHandlerではない）。"""
    main_module.setup_logging(tmp_path)

    timed_handlers = [
        h for h in logging.getLogger().handlers
        if isinstance(h, TimedRotatingFileHandler)
    ]
    assert len(timed_handlers) == 1, (
        "setup_logging は TimedRotatingFileHandler を1つ取り付けるべき"
    )

    handler = timed_handlers[0]
    # Windowsローテ事故対策のキー設定を検証
    assert handler.when == "MIDNIGHT", "深夜ローテで取引と衝突しないこと"
    assert handler.backupCount == 14, "14日分のバックアップを保持すること"
    assert handler.encoding == "utf-8", "UTF-8で書き込みすること"
    # delay=True: 起動直後の空ファイル生成を抑止
    assert handler.delay is True, "delay=Trueで初回書き込みまでファイルを開かないこと"


def test_setup_logging_creates_log_dir(tmp_path):
    """setup_logging() は log_dir が無くても自動作成する。"""
    log_dir = tmp_path / "data"
    assert not log_dir.exists()
    main_module.setup_logging(log_dir)
    assert log_dir.exists() and log_dir.is_dir()


def test_setup_logging_writes_to_trading_log(tmp_path):
    """setup_logging 後にロガーに出力すると trading.log にflushされる。"""
    main_module.setup_logging(tmp_path)
    logger = logging.getLogger("test_setup_logging")
    logger.info("テストメッセージ")

    # delay=Trueなので明示的にflushして書き込みを発火
    for h in logging.getLogger().handlers:
        try:
            h.flush()
        except Exception:
            pass

    log_file = tmp_path / "trading.log"
    assert log_file.exists(), "trading.log が生成されること"
    content = log_file.read_text(encoding="utf-8")
    assert "テストメッセージ" in content
