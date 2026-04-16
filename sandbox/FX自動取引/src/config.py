"""
FX自動取引システム — 設定管理モジュール

全てのリスクパラメータ・定数・環境変数をここで一元管理する。
doc 04 セクション4.1 準拠。
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# .envファイルの読み込み（プロジェクトルートから検索）
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


# ============================================================
# リスクパラメータ（doc 04 セクション4.1）
# ============================================================

# --- 1トレードあたりのリスク ---
MAX_RISK_PER_TRADE: float = 0.01       # 口座資金の1%
MAX_RISK_PER_TRADE_HARD: float = 0.02  # 絶対上限2%

# --- レバレッジ ---
MAX_LEVERAGE: int = 10                 # 自主制限（法的上限25倍の40%）

# --- ドローダウン制御（5段階） ---
DRAWDOWN_LEVELS: dict[float, str] = {
    0.05: "WARNING",      # 5%: 警告通知
    0.10: "REDUCE",       # 10%: ポジションサイズ半減
    0.15: "MINIMUM",      # 15%: 最小ロットのみ
    0.20: "STOP",         # 20%: 全停止（ハードリミット）
    0.25: "EMERGENCY",    # 25%: 全ポジション強制決済
}

# --- 日次・週次・月次損失上限 ---
MAX_DAILY_LOSS: float = 0.02           # 日次: 口座の2%
MAX_WEEKLY_LOSS: float = 0.05          # 週次: 口座の5%
MAX_MONTHLY_LOSS: float = 0.10         # 月次: 口座の10%

# --- 連続負け制限 ---
MAX_CONSECUTIVE_LOSSES: int = 5        # 5連敗で一時停止

# --- ポジション制限 ---
MAX_OPEN_POSITIONS: int = 6            # 最大同時ポジション数（6ペア並行対応）
MAX_CORRELATION_EXPOSURE: int = 2      # 相関通貨ペアの最大同時保有数

# 通貨ペア相関グループ（同じグループ内のペアは相関リスクあり）
CORRELATION_GROUPS: dict[str, list[str]] = {
    "JPY_CROSS": ["USD_JPY", "EUR_JPY", "GBP_JPY"],
    "USD_GROUP": ["USD_JPY", "EUR_USD", "AUD_USD", "GBP_USD"],
}


# ============================================================
# 戦略パラメータ（doc 04 セクション5.1）
# ============================================================

MA_SHORT_PERIOD: int = 20              # 短期MA期間
MA_LONG_PERIOD: int = 50               # 長期MA期間
RSI_PERIOD: int = 14                   # RSI計算期間
RSI_OVERBOUGHT: int = 70               # RSI買われすぎ閾値
RSI_OVERSOLD: int = 30                 # RSI売られすぎ閾値
ATR_PERIOD: int = 14                   # ATR計算期間
ATR_MULTIPLIER: float = 2.0            # ATR損切り乗数
MIN_RISK_REWARD: float = 2.0           # 最小リスクリワード比

# ADXフィルター（Phase 2 F15 追加）
ADX_PERIOD: int = 14                   # ADX計算期間
ADX_THRESHOLD: float = 15.0            # ADXトレンド判定閾値（20→15に緩和、レンジ期シグナル機会確保）

# MFIフィルター（Phase 3 追加）
MFI_PERIOD: int = 14                   # MFI計算期間
MFI_OVERBOUGHT: int = 80              # MFI買われすぎ閾値
MFI_OVERSOLD: int = 20                # MFI売られすぎ閾値
MFI_ENABLED: bool = True              # MFIフィルター有効/無効

# 確信度スコア（Phase 3 追加）
MIN_CONVICTION_SCORE: int = 4          # 最低確信度スコア（4未満は見送り）

# レジーム検出（Phase 3 追加）
REGIME_ADX_TRENDING: float = 20.0      # ADXがこの値以上 → TRENDING（25→20に緩和）
REGIME_ADX_RANGING: float = 15.0       # ADXがこの値未満 → RANGING（20→15に緩和）
REGIME_ATR_VOLATILE_RATIO: float = 2.0 # ATR/中央値ATR がこの値超 → VOLATILE
REGIME_BBW_SQUEEZE_RATIO: float = 0.5  # BBW/平均BBW がこの値未満 → RANGING（スクイーズ）

# Bear Researcher設定（Phase 3 追加）
BEAR_RESEARCHER_ENABLED: bool = True
BEAR_SEVERITY_THRESHOLD: float = 0.4     # この値以上でpenalty適用
BEAR_MAX_PENALTY: float = 0.5            # 最大減点（倍率0.5まで）
BEAR_DIVERGENCE_LOOKBACK: int = 5        # ダイバージェンス検出の振り返り期間
BEAR_SR_ATR_MULTIPLIER: float = 1.5      # サポレジ接近判定のATR倍率


# ============================================================
# タイムフレーム
# ============================================================

MAIN_TIMEFRAME: str = "H1"             # メインタイムフレーム（1時間足、H4→H1に変更しシグナル頻度向上）

# デフォルト監視通貨ペア（複数ペア同時監視用）
DEFAULT_INSTRUMENTS: list[str] = [
    "USD_JPY", "EUR_USD", "GBP_JPY",
    "AUD_USD", "EUR_JPY", "GBP_USD",
]


# ============================================================
# API設定（CLAUDE.md リトライ・タイムアウト規約準拠）
# ============================================================

API_TIMEOUT: int = 30                  # APIタイムアウト（秒）
API_MAX_RETRIES: int = 3               # 最大リトライ回数


# ============================================================
# キルスイッチ閾値（doc 04 セクション4.2）
# ============================================================

KILL_ATR_MULTIPLIER: float = 3.0       # ATR通常の3倍でボラティリティキル
KILL_SPREAD_MULTIPLIER: float = 5.0    # スプレッド通常の5倍でスプレッドキル
KILL_API_DISCONNECT_SEC: int = 30      # API切断30秒で全ポジション決済
KILL_COOLDOWN_MINUTES: int = 5         # volatility/spreadキルの最低クールダウン時間（分）


# ============================================================
# MT5設定（外為ファイネスト用）
# ============================================================

MT5_MAGIC_NUMBER: int = 234000          # EA識別番号
MT5_DEVIATION: int = 20                 # 最大スリッページ（ポイント）
MT5_SYMBOL_SUFFIX: str = "-"            # 外為ファイネストのシンボル接尾辞
MT5_LOT_UNIT: int = 100_000             # 1ロット = 100,000通貨


# ============================================================
# AI市場分析設定（Phase 3 追加）
# ============================================================

AI_MODEL_ID: str = "claude-sonnet-4-20250514"   # 市場分析に使用するモデル（バージョン固定）
AI_ANALYSIS_DIR: Path = _project_root / "data"  # market_analysis.json の配置先
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# トレード事後分析（L1）
POSTMORTEM_ENABLED: bool = True           # 事後分析の有効/無効
POSTMORTEM_MODEL_ID: str = AI_MODEL_ID    # 事後分析に使用するモデル


# ============================================================
# データベース
# ============================================================

DB_PATH: Path = _project_root / "data" / "fx_trading.db"


# ============================================================
# Telegram Bot 設定
# ============================================================

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ENABLED: bool = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


# ============================================================
# Slack Webhook 設定
# ============================================================

SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_ALERTS_WEBHOOK_URL: str = os.getenv("SLACK_ALERTS_WEBHOOK_URL", "")
SLACK_ENABLED: bool = bool(SLACK_WEBHOOK_URL)


# ============================================================
# バリデーション
# ============================================================

@dataclass
class ConfigValidationError:
    """設定バリデーションエラーの詳細"""
    field_name: str
    message: str


def validate_config() -> list[ConfigValidationError]:
    """
    設定値のバリデーションを実行する。

    Returns:
        バリデーションエラーのリスト。空なら全て正常。
    """
    errors: list[ConfigValidationError] = []

    # --- リスクパラメータの範囲チェック ---
    if not (0 < MAX_RISK_PER_TRADE <= 1):
        errors.append(ConfigValidationError(
            "MAX_RISK_PER_TRADE",
            f"MAX_RISK_PER_TRADEは0〜1の範囲内である必要があります。現在の値: {MAX_RISK_PER_TRADE}"
        ))

    if not (0 < MAX_RISK_PER_TRADE_HARD <= 1):
        errors.append(ConfigValidationError(
            "MAX_RISK_PER_TRADE_HARD",
            f"MAX_RISK_PER_TRADE_HARDは0〜1の範囲内である必要があります。現在の値: {MAX_RISK_PER_TRADE_HARD}"
        ))

    if MAX_RISK_PER_TRADE > MAX_RISK_PER_TRADE_HARD:
        errors.append(ConfigValidationError(
            "MAX_RISK_PER_TRADE",
            f"MAX_RISK_PER_TRADE({MAX_RISK_PER_TRADE})がMAX_RISK_PER_TRADE_HARD({MAX_RISK_PER_TRADE_HARD})を超えています。"
        ))

    if not (1 <= MAX_LEVERAGE <= 25):
        errors.append(ConfigValidationError(
            "MAX_LEVERAGE",
            f"MAX_LEVERAGEは1〜25の範囲内である必要があります（日本の法規制上限25倍）。現在の値: {MAX_LEVERAGE}"
        ))

    if not (0 < MAX_DAILY_LOSS <= 1):
        errors.append(ConfigValidationError(
            "MAX_DAILY_LOSS",
            f"MAX_DAILY_LOSSは0〜1の範囲内である必要があります。現在の値: {MAX_DAILY_LOSS}"
        ))

    if not (0 < MAX_WEEKLY_LOSS <= 1):
        errors.append(ConfigValidationError(
            "MAX_WEEKLY_LOSS",
            f"MAX_WEEKLY_LOSSは0〜1の範囲内である必要があります。現在の値: {MAX_WEEKLY_LOSS}"
        ))

    if not (0 < MAX_MONTHLY_LOSS <= 1):
        errors.append(ConfigValidationError(
            "MAX_MONTHLY_LOSS",
            f"MAX_MONTHLY_LOSSは0〜1の範囲内である必要があります。現在の値: {MAX_MONTHLY_LOSS}"
        ))

    # --- 戦略パラメータのチェック ---
    if MA_SHORT_PERIOD >= MA_LONG_PERIOD:
        errors.append(ConfigValidationError(
            "MA_SHORT_PERIOD",
            f"短期MA({MA_SHORT_PERIOD})は長期MA({MA_LONG_PERIOD})より短い必要があります。"
        ))

    if not (0 < RSI_OVERSOLD < RSI_OVERBOUGHT < 100):
        errors.append(ConfigValidationError(
            "RSI_OVERSOLD/RSI_OVERBOUGHT",
            f"RSI閾値は 0 < OVERSOLD({RSI_OVERSOLD}) < OVERBOUGHT({RSI_OVERBOUGHT}) < 100 である必要があります。"
        ))

    if ATR_MULTIPLIER <= 0:
        errors.append(ConfigValidationError(
            "ATR_MULTIPLIER",
            f"ATR_MULTIPLIERは正の値である必要があります。現在の値: {ATR_MULTIPLIER}"
        ))

    if MIN_RISK_REWARD <= 0:
        errors.append(ConfigValidationError(
            "MIN_RISK_REWARD",
            f"MIN_RISK_REWARDは正の値である必要があります。現在の値: {MIN_RISK_REWARD}"
        ))

    return errors


def validate_or_raise() -> None:
    """
    設定バリデーションを実行し、エラーがあれば例外を送出する。

    Raises:
        SystemExit: バリデーションエラーが1つ以上ある場合
    """
    errors = validate_config()
    if errors:
        logger.error("設定バリデーションエラーが検出されました:")
        for err in errors:
            logger.error(f"  [{err.field_name}] {err.message}")
        raise SystemExit(
            f"設定エラー: {len(errors)}件のバリデーションエラーがあります。.envファイルと設定値を確認してください。"
        )
