"""
FX自動取引システム — AI市場環境アドバイザー

Claudeスケジューラーが日次で生成する市場環境分析（market_analysis.json）を読み込み、
トレーディングループにAIバイアスを提供する。

AIは最終判断をしない。既存の戦略シグナルに対して:
- CONFIRM: AIがシグナルと同方向 → そのまま実行
- CONTRADICT: AIがシグナルと逆方向 → ポジションサイズを縮小
- NEUTRAL: AI判断なし → そのまま実行
- REJECT: 重大リスク → シグナルを無視

リスク管理はコードロジック（RiskManager/KillSwitch）が最終ゲート。
AIがリスク管理を上書きすることは絶対にない。
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# AI分析ファイルの有効期限（時間）
MAX_ANALYSIS_AGE_HOURS = 24


class AIBias:
    """AI分析に基づくトレードバイアス"""

    def __init__(
        self,
        direction: str,  # "bullish", "bearish", "neutral"
        confidence: float,  # 0.0 - 1.0
        regime: str,  # "trending", "ranging", "volatile", "unknown"
        key_levels: dict,  # {"support": float, "resistance": float}
        reasoning: str,  # AI の判断理由
        timestamp: str,  # 分析生成時刻（ISO 8601）
    ):
        self.direction = direction
        self.confidence = confidence
        self.regime = regime
        self.key_levels = key_levels
        self.reasoning = reasoning
        self.timestamp = timestamp

    def evaluate_signal(self, signal_direction: str) -> str:
        """
        既存戦略のシグナルをAIバイアスで評価する

        Args:
            signal_direction: "BUY" or "SELL"

        Returns:
            "CONFIRM" / "CONTRADICT" / "NEUTRAL" / "REJECT"
        """
        # 信頼度が低い場合はNEUTRAL
        if self.confidence < 0.3:
            return "NEUTRAL"

        # 市場環境が不明な場合はNEUTRAL
        if self.regime == "unknown":
            return "NEUTRAL"

        # ボラティリティが異常に高い場合はREJECT
        if self.regime == "volatile" and self.confidence > 0.7:
            logger.warning(
                "AI: 高ボラティリティ環境を検出（confidence=%.2f）。シグナルを拒否",
                self.confidence,
            )
            return "REJECT"

        # 方向の一致チェック
        signal_is_buy = signal_direction == "BUY"
        ai_is_bullish = self.direction == "bullish"
        ai_is_bearish = self.direction == "bearish"

        if self.direction == "neutral":
            return "NEUTRAL"

        if (signal_is_buy and ai_is_bullish) or (not signal_is_buy and ai_is_bearish):
            return "CONFIRM"

        if (signal_is_buy and ai_is_bearish) or (not signal_is_buy and ai_is_bullish):
            return "CONTRADICT"

        return "NEUTRAL"

    def position_size_multiplier(self, evaluation: str) -> float:
        """
        評価結果に基づくポジションサイズ倍率

        Returns:
            0.0 - 1.5 の倍率
        """
        multipliers = {
            "CONFIRM": min(1.0 + self.confidence * 0.5, 1.5),  # 最大1.5倍
            "CONTRADICT": max(0.5 - self.confidence * 0.3, 0.2),  # 最小0.2倍
            "NEUTRAL": 1.0,
            "REJECT": 0.0,  # 取引しない
        }
        return multipliers.get(evaluation, 1.0)

    def __repr__(self) -> str:
        return (
            f"AIBias(direction={self.direction}, confidence={self.confidence:.2f}, "
            f"regime={self.regime})"
        )


class AIAdvisor:
    """
    AI市場環境分析を読み込み、トレードバイアスを提供する

    分析ファイルはClaudeスケジューラーが日次で生成し、
    gitリポジトリ経由でVPSに配信される。
    """

    def __init__(self, analysis_dir: Path):
        """
        Args:
            analysis_dir: market_analysis.json が配置されるディレクトリ
        """
        self._analysis_dir = analysis_dir
        self._last_bias: Optional[AIBias] = None
        self._analysis_path = analysis_dir / "market_analysis.json"

    def get_bias(self, instrument: str = "USD_JPY") -> Optional[AIBias]:
        """
        最新のAI分析を読み込んでバイアスを返す

        Args:
            instrument: 通貨ペア

        Returns:
            AIBias または None（分析ファイルがない/期限切れの場合）
        """
        if not self._analysis_path.exists():
            logger.debug("AI分析ファイルが見つかりません: %s", self._analysis_path)
            return None

        try:
            with open(self._analysis_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("AI分析ファイルの読み込みに失敗: %s", e)
            return None

        # 対象通貨ペアの分析を取得
        analysis = data.get(instrument) or data.get(instrument.replace("_", ""))
        if analysis is None:
            # トップレベルにあるかもしれない（単一通貨ペアの場合）
            if "direction" in data:
                analysis = data
            else:
                logger.debug("通貨ペア %s の分析が見つかりません", instrument)
                return None

        # 有効期限チェック
        timestamp = analysis.get("timestamp", "")
        if timestamp:
            try:
                analysis_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                age_hours = (
                    datetime.now(timezone.utc) - analysis_time
                ).total_seconds() / 3600
                if age_hours > MAX_ANALYSIS_AGE_HOURS:
                    logger.info(
                        "AI分析が期限切れです（%.1f時間経過、上限%d時間）",
                        age_hours,
                        MAX_ANALYSIS_AGE_HOURS,
                    )
                    return None
            except ValueError:
                logger.warning("AI分析のタイムスタンプが不正: %s", timestamp)

        # AIBiasオブジェクトを生成
        bias = AIBias(
            direction=analysis.get("direction", "neutral"),
            confidence=float(analysis.get("confidence", 0.0)),
            regime=analysis.get("regime", "unknown"),
            key_levels=analysis.get("key_levels", {}),
            reasoning=analysis.get("reasoning", ""),
            timestamp=timestamp,
        )

        self._last_bias = bias
        logger.info("AI分析を読み込みました: %s", bias)
        return bias

    @property
    def last_bias(self) -> Optional[AIBias]:
        """最後に読み込んだバイアス"""
        return self._last_bias
