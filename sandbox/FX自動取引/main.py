"""
FX自動取引システム — エントリーポイント

MT5ブローカー接続 → MA Crossover + ADX戦略 → ペーパートレード実行
VPSのタスクスケジューラから自動起動される。
"""
import argparse
import logging
import sys
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.config import MAIN_TIMEFRAME
from src.mt5_client import Mt5Client
from src.position_manager import PositionManager
from src.risk_manager import RiskManager
from src.strategy.ma_crossover import RsiMaCrossover
from src.trading_loop import TradingLoop


def setup_logging(log_dir: Path):
    """ログ設定"""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "trading.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="FX自動取引システム")
    parser.add_argument(
        "--instrument", default="USD_JPY", help="取引通貨ペア（デフォルト: USD_JPY）"
    )
    parser.add_argument(
        "--granularity", default=MAIN_TIMEFRAME, help="時間足（デフォルト: H4）"
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="チェック間隔（秒、デフォルト: 60）"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="接続テストのみ（取引しない）"
    )
    args = parser.parse_args()

    # ログ設定
    data_dir = project_root / "data"
    setup_logging(data_dir)
    logger = logging.getLogger(__name__)

    logger.info("=== FX自動取引システム起動 ===")
    logger.info(f"通貨ペア: {args.instrument}")
    logger.info(f"時間足: {args.granularity}")
    logger.info(f"チェック間隔: {args.interval}秒")
    logger.info(f"ドライラン: {args.dry_run}")

    # MT5接続
    with Mt5Client() as broker:
        account = broker.get_account_summary()
        logger.info(f"口座接続成功: {account}")

        if args.dry_run:
            logger.info("ドライラン完了。取引は行いません。")
            return

        # コンポーネント初期化
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
        strategy = RsiMaCrossover()

        # トレーディングループ
        loop = TradingLoop(
            broker_client=broker,
            position_manager=position_manager,
            risk_manager=risk_manager,
            strategy=strategy,
            instrument=args.instrument,
            granularity=args.granularity,
            check_interval_sec=args.interval,
        )

        logger.info("トレーディングループ開始")
        try:
            loop.start()
        except Exception as e:
            logger.exception(f"トレーディングループ異常終了: {e}")
            raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"致命的エラー: {e}")
        sys.exit(1)
