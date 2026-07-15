import json
from pathlib import Path
from typing import List, Dict, Any

class HMComparator:
    def __init__(self, data_dir: str = "data/hms"):
        self.data_dir = Path(data_dir)

    def load_hm_data(self, hm_name: str) -> Dict[str, Any]:
        """ハウスメーカーの解析データを読み込む"""
        file_path = self.data_dir / hm_name / "analysis.json"
        if not file_path.exists():
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_comparison_markdown(self, hm_names: List[str]) -> str:
        """指定されたハウスメーカーの比較表(Markdown)を生成する"""
        all_data = {name: self.load_hm_data(name) for name in hm_names}
        
        # カテゴリ一覧
        categories = {
            "price": "価格（透明性・LCC）",
            "performance": "性能（断熱・耐震）",
            "warranty": "保証（期間・条件）",
            "specifications": "仕様（設備・内装）"
        }

        # ヘッダー作成
        headers = ["カテゴリ"] + hm_names
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("|" + "---|" * (len(hm_names) + 1))

        # 各カテゴリの行を作成
        for cat_key, cat_name in categories.items():
            row = [cat_name]
            for hm in hm_names:
                data = all_data.get(hm, {})
                aspect = data.get("aspects", {}).get(cat_key, {})
                level = aspect.get("level", "未確認")
                summary = aspect.get("summary", "-")
                
                # レベルに応じたバッジ風表示
                level_icon = "🟢" if level == "高" else "🟡" if level == "中" else "🔴" if level == "低" else "⚪"
                row.append(f"{level_icon} **{level}**<br>{summary}")
            
            lines.append("| " + " | ".join(row) + " |")

        # 未確認・懸念事項のセクション
        lines.append("\n### ⚠️ 未回答の懸念・沈黙の論点")
        for hm in hm_names:
            data = all_data.get(hm, {})
            missing = data.get("missing_points", [])
            if missing:
                lines.append(f"\n#### 【{hm}】")
                for point in missing:
                    lines.append(f"- {point}")

        return "\n".join(lines)

if __name__ == "__main__":
    # テスト表示
    comparator = HMComparator()
    # 既存のデータ（住友不動産）と、未作成のダミー（建新など）を想定
    print(comparator.generate_comparison_markdown(["住友不動産"]))
