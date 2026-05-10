"""SPEC v2 ゼロベース再構築モジュール

OPERATING_MODEL.md v2.1 の 15 スキームをコード資産化する。
現状確定済み: § 2-1 季節判定 (seasonal_detection.py)
"""

from src.spec_v2.seasonal_detection import SeasonalDetector, SeasonRegime

__all__ = ["SeasonalDetector", "SeasonRegime"]
