"""エンジンの疎通デモ（API キー不要・モック応答）。

実行: python3 demo.py
実 YAML ペルソナを読み込み、Council を1回流して進行（誰が・どのフェーズで喋るか）を表示する。
本番の応答にするには MockLLMClient を AnthropicClient(api_key=...) に差し替えるだけ。
"""

from pathlib import Path

from core import Council, MockLLMClient, load_personas

HERE = Path(__file__).resolve().parent


def main() -> None:
    personas = load_personas(HERE / "personas")
    print(f"読み込んだペルソナ {len(personas)} 体: " + ", ".join(p.display_name for p in personas))
    print()

    # 思考スタイル4体＋司会＋議長で討論（経営者/哲学者を混ぜたい場合はここに追加するだけ）
    use_ids = {"moderator", "logic", "idea", "empathy", "chair"}
    council = Council(
        [p for p in personas if p.id in use_ids],
        MockLLMClient(),  # ← AnthropicClient(api_key=...) に差し替えれば本番
        rounds_per_phase=1,
    )

    topic = "空き家を活用した新規事業案を出してほしい"
    print(f"議題: {topic}\n" + "=" * 60)
    for turn in council.run(topic):
        print(f"[{turn.phase:<8}] {turn.speaker_name}: {turn.content}")


if __name__ == "__main__":
    main()
