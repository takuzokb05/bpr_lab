"""
データベースの内容を確認
"""
from database import Database

db = Database()

print("=" * 80)
print("データベース確認")
print("=" * 80)

# ルーム一覧
rooms = db.get_all_rooms()
print(f"\n📂 ルーム数: {len(rooms)}")
for room in rooms:
    print(f"\nルームID: {room['id']}")
    print(f"タイトル: {room['title']}")
    print(f"作成日時: {room['created_at']}")
    
    # メッセージ数
    messages = db.get_room_messages(room['id'])
    print(f"メッセージ数: {len(messages)}")
    
    # 最新5件のメッセージを表示
    if messages:
        print("\n最新のメッセージ:")
        for msg in messages[-5:]:
            role = "ユーザー" if msg['role'] == 'user' else msg.get('agent_name', '不明')
            print(f"  [{role}] {msg['content'][:50]}...")

# エージェント一覧
agents = db.get_all_agents()
print(f"\n\n🤖 エージェント数: {len(agents)}")
for agent in agents:
    print(f"  - {agent['icon']} {agent['name']} ({agent['provider']}/{agent['model']})")

print("\n" + "=" * 80)
