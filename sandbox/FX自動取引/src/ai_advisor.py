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
    """AI分析に基づくトレードバイアス

    T5: A/B 検証のため `decision` / `reasons` を最後の評価結果として保持する。
    `evaluate_signal()` は副作用としてこれらを更新する。
    """

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
        # T5: A/B 集計用 — 最後に評価したシグナルでの判定結果を保持
        self.decision: Optional[str] = None
        self.reasons: Optional[str] = None

    def evaluate_signal(self, signal_direction: str) -> str:
        """
        既存戦略のシグナルをAIバイアスで評価する。

        副作用: self.decision / self.reasons を更新する（A/B 集計の永続化用）。

        Args:
            signal_direction: "BUY" or "SELL"

        Returns:
            "CONFIRM" / "CONTRADICT" / "NEUTRAL" / "REJECT"
        """
        decision, reasons = self._classify(signal_direction)
        self.decision = decision
        self.reasons = reasons
        return decision

    def _classify(self, signal_direction: str) -> tuple[str, str]:
        """シグナル判定ロジック本体。(decision, reasons) を返す。"""
        # 信頼度が低い場合はNEUTRAL
        if self.confidence < 0.3:
            return "NEUTRAL", f"low_confidence({self.confidence:.2f})"

        # 市場環境が不明な場合はNEUTRAL
        if self.regime == "unknown":
            return "NEUTRAL", "regime_unknown"

        # ボラティリティが異常に高い場合はREJECT
        if self.regime == "volatile" and self.confidence > 0.7:
            logger.warning(
                "AI: 高ボラティリティ環境を検出（confidence=%.2f）。シグナルを拒否",
                self.confidence,
            )
            return "REJECT", f"volatile_high_conf({self.confidence:.2f})"

        # 方向の一致チェック
        signal_is_buy = signal_direction == "BUY"
        ai_is_bullish = self.direction == "bullish"
        ai_is_bearish = self.direction == "bearish"

        if self.direction == "neutral":
            return "NEUTRAL", "ai_direction_neutral"

        if (signal_is_buy and ai_is_bullish) or (not signal_is_buy and ai_is_bearish):
            return (
                "CONFIRM",
                f"aligned({signal_direction}/{self.direction})",
            )

        if (signal_is_buy and ai_is_bearish) or (not signal_is_buy and ai_is_bullish):
            return (
                "CONTRADICT",
                f"opposite({signal_direction}/{self.direction})",
            )

        return "NEUTRAL", "fallthrough"

    def to_record(self) -> dict:
        """trades テーブルに永続化するための dict 表現を返す。

        evaluate_signal() を一度も呼んでいない場合 decision/reasons は None になる。
        """
        return {
            "ai_decision": self.decision,
            "ai_confidence": float(self.confidence),
            "ai_reasons": self.reasons,
            "ai_direction": self.direction,
            "ai_regime": self.regime,
        }

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
