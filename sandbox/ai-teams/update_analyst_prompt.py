from database import Database

def update_analyst():
    db = Database()
    agents = db.get_all_agents()
    
    new_role = """# ペルソナ
あなたはデータサイエンティスト兼ビジネスアナリストです。「数字は嘘をつかない」を信条とし、感覚や直感ではなく、自ら設定した論理的仮定とデータに基づいた意思決定を推進します。

# 専門性
- データ分析・統計解析、KPI設計、実験設計

# 行動指針（最優先）
- **自律的仮定の設定**: データが未知の場合でも「業界標準や類似モデルから、ここでは〇〇という数値を仮定する」と自ら前提を置き、議論を前進させる。
- **主体的提案**: 「〜が必要」と受動的に言うのではなく、「〜を検証するために△△というKPIを設計し、目標値をXX%に設定すべきである」と断定・提案する。

# 発言スタイル
- 「〜を検証するため、ここでは市場規模を〇〇と仮定し、△△のデータを軸に分析します」
- 「具体的な目標値はXX%、測定手法は〜を採用します」

# 制約
- **出力制限なし**: 専門的知見を尽くし、論理が完結するまで長文で詳述すること。
- **必須要素**: 測定方法、具体的なKPI、およびそれらを導き出すための「仮説/仮定」を必ず含める。"""

    updated_count = 0
    for a in agents:
        # データアナリスト、もしくはそれに類するエージェントを更新
        if "データ" in a['name'] or "アナリスト" in a['name']:
            print(f"Updating agent: {a['name']} (ID: {a['id']})")
            # 既存の値を保持しつつ、roleだけ更新
            db.update_agent(
                a['id'], 
                a['name'], 
                a['icon'], 
                a['color'], 
                new_role, 
                a['model'], 
                a['provider'], 
                a['category']
            )
            updated_count += 1
            
    if updated_count == 0:
        print("No Data Analyst found. Creating one...")
        db.create_agent(
            "📊 データアナリスト",
            "📊",
            "#F44336",
            new_role,
            "default",
            "openai",
            "logic"
        )
        print("Created new Data Analyst agent.")
    else:
        print(f"Updated {updated_count} agents.")

if __name__ == "__main__":
    update_analyst()
