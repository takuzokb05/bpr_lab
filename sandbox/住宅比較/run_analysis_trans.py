import os
import json
from pathlib import Path
from src.analyzer import HMAnalyzer

def run_actual_analysis():
    # ログファイルの読み込み
    log_path = Path(r"C:\Users\takuz\プロジェクト\bpr_lab\sandbox\住宅比較\01-31 相談ミーティング_ 住宅購入予算・施工品質・土地条件の総合検討（2026-01-31-transcript.txt")
    
    if not log_path.exists():
        print(f"Error: Log file not found at {log_path}")
        return

    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()

    # 住友不動産の分析として実行
    analyzer = HMAnalyzer()
    print("Analyzing Sumitomo Real Estate (住友不動産) logs...")
    
    # トークン制限を考慮し、重要な部分を抽出するか、全体を渡す（Claudeであれば十分入る）
    result = analyzer.analyze_logs("住友不動産", [log_content])
    
    print("\n--- Analysis Result ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nSaved to: data/hms/住友不動産/analysis.json")

if __name__ == "__main__":
    run_actual_analysis()
