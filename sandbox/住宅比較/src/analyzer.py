import os
import json
from pathlib import Path
from typing import Dict, Any, List
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class HMAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.data_dir = Path("data/hms")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.mapping_file = Path("config/name_mapping.json")
        self.aliases = self._load_aliases()

    def _load_aliases(self) -> Dict[str, str]:
        if self.mapping_file.exists():
            with open(self.mapping_file, "r", encoding="utf-8") as f:
                return json.load(f).get("aliases", {})
        return {}

    def resolve_name(self, name: str) -> str:
        """エイリアスを解決して正式名称を返す"""
        return self.aliases.get(name, name)

    def analyze_logs(self, hm_display_name: str, log_texts: List[str]) -> Dict[str, Any]:
        """
        Claude APIを使用してログを解析し、F1/F2に必要なデータを抽出する。
        """
        hm_name = self.resolve_name(hm_display_name)
        prompt = f"""
以下のハウスメーカー「{hm_name}」に関する営業との会話ログや資料テキストを解析してください。

要件:
1. 「価格」「性能」「保証」「仕様」の4カテゴリについて、説明の解像度（高・中・低）と把握内容を抽出すること。
2. 営業側の具体的な主張をリストアップすること。
3. 施主がまだ聞けていない、または曖昧なままの「懸念点・未確認事項」を抽出すること。

出力フォーマットは以下のJSON構造に厳密に従ってください:
{{
  "hm_name": "{hm_name}",
  "aspects": {{
    "price": {{ "level": "高/中/低/未確認", "summary": "...", "raw_claims": ["..."] }},
    "performance": {{ "level": "高/中/低/未確認", "summary": "...", "raw_claims": ["..."] }},
    "warranty": {{ "level": "高/中/低/未確認", "summary": "...", "raw_claims": ["..."] }},
    "specifications": {{ "level": "高/中/低/未確認", "summary": "...", "raw_claims": ["..."] }}
  }},
  "missing_points": ["..."]
}}

ログ内容:
{" ".join(log_texts)}
"""
        response = self.client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=2000,
            system="あなたは注文住宅の専門コンサルタントAIです。営業のトークから事実と未踏の論点を分離するプロフェッショナルです。",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 簡易的にJSON部分を抽出（実際にはもう少し堅牢な処理が必要）
        content = response.content[0].text
        data = json.loads(content[content.find('{'):content.rfind('}')+1])
        
        # データの永続化
        self.save_data(hm_name, data)
        return data

    def save_data(self, hm_name: str, data: Dict[str, Any]):
        path = self.data_dir / hm_name
        path.mkdir(exist_ok=True)
        with open(path / "analysis.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # テスト実行用のコード（必要に応じて）
    pass
