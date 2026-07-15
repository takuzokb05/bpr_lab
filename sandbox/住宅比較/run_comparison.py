from src.comparator import HMComparator
from pathlib import Path

def main():
    comparator = HMComparator()
    # 現時点の主要2社を比較
    hm_list = ["住友不動産", "建新"]
    
    markdown_report = comparator.generate_comparison_markdown(hm_list)
    
    report_path = Path("比較レポート.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ハウスメーカー比較レポート (PoC)\n\n")
        f.write(markdown_report)
    
    print(f"Report generated: {report_path.absolute()}")

if __name__ == "__main__":
    main()
