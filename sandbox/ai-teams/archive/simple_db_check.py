"""
シンプルなDB確認
"""
import sqlite3

conn = sqlite3.connect('ai_teams.db')
cursor = conn.cursor()

# ルーム数
cursor.execute("SELECT COUNT(*) FROM rooms")
room_count = cursor.fetchone()[0]
print(f"Rooms: {room_count}")

# メッセージ数
cursor.execute("SELECT COUNT(*) FROM messages")
msg_count = cursor.fetchone()[0]
print(f"Messages: {msg_count}")

# 最新5件のメッセージ
cursor.execute("SELECT id, room_id, role, content FROM messages ORDER BY id DESC LIMIT 5")
messages = cursor.fetchall()
print(f"\nLatest messages:")
for msg in messages:
    print(f"  ID:{msg[0]} Room:{msg[1]} Role:{msg[2]} Content:{msg[3][:30]}...")

conn.close()
