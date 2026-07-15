import os
import sys
import unittest
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.analyzer import HMAnalyzer

class TestHMAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = HMAnalyzer()
        self.test_hm = "テストハウス"
        self.test_logs = [
            "営業：弊社の断熱材は高性能グラスウールです。UA値は0.46を標準としています。",
            "施主：地震への強さはどうですか？",
            "営業：耐震等級3は当然クリアしていますが、独自の制震ダンパーも備えています。",
            "施主：価格はどれくらいになりますか？",
            "営業：仕様によりますが、坪単価80万円程度を見ていただければ。"
        ]

    def test_directory_creation(self):
        """ディレクトリが作成されるか確認"""
        self.assertTrue(Path("data/hms").exists())

    @unittest.skip("API call cost reduction - run only when needed")
    def test_analyze_logs(self):
        """APIを呼び出して解析結果が正しく生成されるか確認（注意：API料金が発生します）"""
        result = self.analyzer.analyze_logs(self.test_hm, self.test_logs)
        self.assertEqual(result["hm_name"], self.test_hm)
        self.assertIn("aspects", result)
        self.assertIn("performance", result["aspects"])
        self.assertTrue(Path(f"data/hms/{self.test_hm}/analysis.json").exists())

if __name__ == "__main__":
    unittest.main()
