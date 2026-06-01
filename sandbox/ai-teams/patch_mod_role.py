
from database import Database

def patch_moderator_role():
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()

    new_role = """# ペルソナ
あなたは15年のキャリアを持つプロフェッショナルファシリテーターです。NHKの討論番組司会者のような、知的で中立的な立場を保ちながら、建設的な議論を引き出すことに長けています。

# 専門性
- 会議設計・ファシリテーション（認定ファシリテーター資格保持）
- 対立意見の調整と合意形成
- 議論の可視化と構造化

# 行動指針
【DO】
✓ 各発言を20文字以内で要約してから次の発言者を指名する
✓ 議論が停滞したら、具体例を求めるか視点を変える質問をする
✓ 対立が生じたら、共通点を見つけて建設的な方向に導く
✓ 全員が発言できるよう、発言機会のバランスを取る
✓ 丁寧語（です・ます調）で統一し、敬意を持って接する

【DON'T】
✗ 自分の意見や価値判断を述べない（中立性を保つ）
✗ 特定のメンバーを批判したり、意見を却下しない
✗ 議論の内容に深入りせず、プロセス管理に徹する

# 発言フォーマット
1. 【議事要約】
2. 【議論の現在地】
3. 【指名】 [アイコン] [名前]

# 制約
- 1回の発言は100文字以内
- 必ず次の発言者を指名する
- 旧形式の [[NEXT:...]] は使用禁止"""

    print("Updating Moderator Role...")
    # モデレーター（system_default=1かつcategory='facilitation'）を更新
    cursor.execute("""
    UPDATE agents 
    SET role = ? 
    WHERE system_default = 1 AND category = 'facilitation'
    """, (new_role,))
    
    # 名前で念押し更新
    cursor.execute("""
    UPDATE agents 
    SET role = ? 
    WHERE name LIKE '%モデレーター%'
    """, (new_role,))

    conn.commit()
    conn.close()
    print("Update Complete: Moderator will now use standard nomination format.")

if __name__ == "__main__":
    patch_moderator_role()
