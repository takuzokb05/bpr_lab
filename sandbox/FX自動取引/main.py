"""
FX自動取引システム — エントリーポイント

MT5ブローカー接続 → MA Crossover + ADX戦略 → ペーパートレード実行
VPSのタスクスケジューラから自動起動される。
マルチペア対応: 複数通貨ペアを並行監視する。
"""
import argparse
import logging
import signal as signal_module
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.ai_advisor import AIAdvisor
from src.bear_researcher import BearResearcher
from src.config import (
    AI_ADVISOR_ENABLED,
    AI_ANALYSIS_DIR,
    BEAR_RESEARCHER_ENABLED,
    DEFAULT_INSTRUMENTS,
    MAIN_TIMEFRAME,
    SLACK_ALERTS_WEBHOOK_URL,
    SLACK_ENABLED,
    TELEGRAM_ENABLED,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from src.mt5_client import Mt5Client
from src.notifier_group import NotifierGroup
from src.position_manager import PositionManager
from src.risk_manager import RiskManager
from src.signal_coordinator import SignalCoordinator
from src.slack_notifier import SlackNotifier
from src.strategy.bollinger_reversal import BollingerReversal
from src.strategy.ma_crossover import RsiMaCrossover
from src.strategy.mtf_pullback import MTFPullback

# 通貨ペアごとの戦略マップ（バックテスト実績に基づく）
# - EUR/USD, USD/JPY M15: MTFPullback (PF 2.0)
# - GBP/JPY M15: BollingerReversal (PF 1.08, 高頻度)
INSTRUMENT_STRATEGY_MAP = {
    "EUR_USD": MTFPullback,
    "USD_JPY": MTFPullback,
    "GBP_JPY": BollingerReversal,
}


def _strategy_for(instrument: str):
    """通貨ペアに対応する戦略クラスを返す。未登録ペアはMTFPullback。"""
    cls = INSTRUMENT_STRATEGY_MAP.get(instrument, MTFPullback)
    return cls()
from src.telegram_notifier import TelegramNotifier, TelegramLogHandler
from src.trading_loop import TradingLoop


def setup_logging(log_dir: Path):
    """ログ設定"""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "trading.log"

    # Windows cp932 環境で em-dash 等がログ出力時に UnicodeEncodeError を起こすのを回避。
    # StreamHandler が書き出す stdout/stderr を UTF-8 に切り替える。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            # Python<3.7 や既にdetachedの場合は無視
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            RotatingFileHandler(
                log_file, encoding="utf-8",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="FX自動取引システム")
    parser.add_argument(
        "--instruments", nargs="+", default=None,
        help="取引通貨ペア（複数指定可、デフォルト: DEFAULT_INSTRUMENTS）"
    )
    parser.add_argument(
        "--instrument", default=None, help="取引通貨ペア（単一指定、後方互換用）"
    )
    parser.add_argument(
        "--granularity", default=MAIN_TIMEFRAME, help="時間足（デフォルト: H1）"
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="チェック間隔（秒、デフォルト: 60）"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="接続テストのみ（取引しない）"
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
    data_dir = project_root / "data"
    setup_logging(data_dir)
    logger = logging.getLogger(__name__)

    logger.info("=== FX自動取引システム起動 ===")
    logger.info(f"通貨ペア: {instruments} ({len(instruments)}ペア)")
    logger.info(f"時間足: {args.granularity}")
    logger.info(f"チェック間隔: {args.interval}秒")
    logger.info(f"ドライラン: {args.dry_run}")

    # MT5接続
    with Mt5Client() as broker:
        account = broker.get_account_summary()
        logger.info(f"口座接続成功: {account}")

        # Telegram通知の初期化（設定がある場合のみ）
        notifier = None
        if TELEGRAM_ENABLED:
            try:
                notifier = TelegramNotifier(
                    bot_token=TELEGRAM_BOT_TOKEN,
                    chat_id=TELEGRAM_CHAT_ID,
                )
                notifier.start()
                # WARNING以上のログを自動転送
                telegram_handler = TelegramLogHandler(notifier)
                logging.getLogger().addHandler(telegram_handler)
                logger.info("Telegram通知を有効化しました")
            except Exception as e:
                logger.warning("Telegram通知の初期化に失敗（取引は継続）: %s", e)
                notifier = None

        if args.dry_run:
            if notifier:
                notifier.notify_bot_status("ドライラン完了")
                notifier.stop()
            logger.info("ドライラン完了。取引は行いません。")
            return

        # 共有コンポーネント初期化
        db_path = data_dir / "fx_trading.db"
        risk_manager = RiskManager(
            account_balance=account["balance"],
            broker_client=broker,
            db_path=db_path,
        )
        position_manager = PositionManager(
            broker_client=broker,
            risk_manager=risk_manager,
            db_path=db_path,
        )

        # AIアドバイザー（market_analysis.jsonがあれば自動読込）
        # LOOSE_MODE: AI_ADVISOR_ENABLED=False の間は起動しない（REJECTで見送られるのを回避）
        if AI_ADVISOR_ENABLED:
            ai_advisor = AIAdvisor(analysis_dir=AI_ANALYSIS_DIR)
            logger.info("AIアドバイザー初期化（分析ディレクトリ: %s）", AI_ANALYSIS_DIR)
        else:
            ai_advisor = None
            logger.info("AIアドバイザーは無効（AI_ADVISOR_ENABLED=False）")

        # Slack通知（取引イベントは #ai-alerts へ）
        slack = None
        if SLACK_ALERTS_WEBHOOK_URL:
            try:
                slack = SlackNotifier(webhook_url=SLACK_ALERTS_WEBHOOK_URL)
                logger.info("Slack通知を有効化しました（#ai-alerts）")
            except Exception as e:
                logger.warning("Slack通知の初期化に失敗（取引は継続）: %s", e)

        # Bear Researcher（逆張り検証）
        bear = BearResearcher() if BEAR_RESEARCHER_ENABLED else None
        if bear:
            logger.info("Bear Researcher（逆張り検証）を有効化しました")

        # 通知グループ（Telegram + Slack を統合）
        notifier_group = NotifierGroup([notifier, slack])

        # シグナル協調（クロスペア相関のLLM評価、全ペア共有）
        coordinator = SignalCoordinator() if len(instruments) > 1 else None
        if coordinator:
            logger.info("SignalCoordinator（クロスペア相関判断）を有効化しました")

        # 各通貨ペアのTradingLoopを生成
        loops: list[TradingLoop] = []
        for instrument in instruments:
            # 戦略は各ペアで独立インスタンス（診断情報が競合しないように）
            # ペアごとに最適戦略を自動選択（INSTRUMENT_STRATEGY_MAP）
            strategy = _strategy_for(instrument)
            logger.info(
                "戦略割当: instrument=%s, strategy=%s",
                instrument, type(strategy).__name__,
            )
            loop = TradingLoop(
                broker_client=broker,
                position_manager=position_manager,
                risk_manager=risk_manager,
                strategy=strategy,
                instrument=instrument,
                granularity=args.granularity,
                check_interval_sec=args.interval,
                notifier=notifier_group,
                ai_advisor=ai_advisor,
                bear_researcher=bear,
                signal_coordinator=coordinator,
            )
            loops.append(loop)

        pairs_str = ", ".join(instruments)
        startup_detail = (
            f"通貨ペア: {pairs_str} ({len(instruments)}ペア) | "
            f"時間足: {args.granularity} | 間隔: {args.interval}秒"
        )
        notifier_group.notify_bot_status("起動", startup_detail)

        # SIGTERMで全ループを安全に停止（タスクスケジューラのkill対応）
        def _shutdown_handler(signum, frame):
            logger.info("シグナル %s 受信: 全ループに停止要求", signum)
            for lp in loops:
                lp.stop()

        signal_module.signal(signal_module.SIGTERM, _shutdown_handler)

        logger.info("トレーディングループ開始（%dペア並行）", len(loops))
        try:
            if len(loops) == 1:
                # 単一ペア: メインスレッドでそのまま実行
                loops[0].start()
            else:
                # マルチペア: スレッドで並行実行
                threads: list[threading.Thread] = []
                for loop in loops:
                    t = threading.Thread(
                        target=loop.start,
                        name=f"loop-{loop._instrument}",
                        daemon=False,
                    )
                    threads.append(t)
                    t.start()
                    logger.info("スレッド起動: %s", t.name)

                # メインスレッドはKeyboardInterruptを待つ
                try:
                    for t in threads:
                        t.join()
                except KeyboardInterrupt:
                    logger.info("KeyboardInterrupt: 全ループに停止要求")
                    for loop in loops:
                        loop.stop()
                    for t in threads:
                        t.join(timeout=10)
        except Exception as e:
            logger.exception(f"トレーディングループ異常終了: {e}")
            raise
        finally:
            notifier_group.notify_bot_status("停止")
            if notifier:
                notifier.stop()  # Telegramスレッドのクリーンアップ


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"致命的エラー: {e}")
        sys.exit(1)
