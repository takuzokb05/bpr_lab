from database import Database
import sqlite3

print("Fixing database...")
db = Database()

# 強制的にテーブル作成を実行してみる
conn = db.get_connection()
cursor = conn.cursor()

try:
    # テーブル作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '🚀',
        prompt TEXT,
        default_agent_ids TEXT
    )
    """)
    print("Templates table created (if not exists).")
    
    # データ確認
    cursor.execute("SELECT count(*) FROM templates")
    count = cursor.fetchone()[0]
    print(f"Current template count: {count}")
    
    if count == 0:
        defaults = [
            ("💡 新規事業ブレスト", "🚀", "革新的なビジネスアイデアを3つ提案し、それぞれの収益性を議論してください。", "[2, 3]"), 
            ("🐛 バグ原因究明", "🛠️", "発生しているシステム障害の原因と解決策を論理的に分析してください。", "[2, 4]"),
            ("🔮 将来戦略会議", "📈", "3年後の市場環境を予測し、我々が取るべき戦略を議論してください。", "[1, 2, 3]")
        ]
        cursor.executemany("INSERT INTO templates (name, icon, prompt, default_agent_ids) VALUES (?, ?, ?, ?)", defaults)
        conn.commit()
        print("Default templates inserted.")
    
except Exception as e:
    print(f"Error: {e}")

conn.close()

# 確認
print("Templates in DB:", db.get_templates())
