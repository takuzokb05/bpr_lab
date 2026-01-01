"""
app.pyの動作を詳細にテスト
"""
from database import Database
import json

db = Database()

print("=" * 80)
print("app.py 動作検証")
print("=" * 80)

# 1. ルーム一覧
rooms = db.get_all_rooms()
print(f"\n📂 ルーム数: {len(rooms)}")

if rooms:
    # 最新のルームを取得
    latest_room = rooms[0]
    print(f"\n最新ルーム:")
    print(f"  ID: {latest_room['id']}")
    print(f"  タイトル: {latest_room['title']}")
    print(f"  作成日時: {latest_room['created_at']}")
    
    # 2. ルームのエージェント
    room_agents = db.get_room_agents(latest_room['id'])
    print(f"\n🤖 参加エージェント数: {len(room_agents)}")
    for agent in room_agents:
        print(f"  - {agent['icon']} {agent['name']}")
    
    # 3. ルームのメッセージ
    messages = db.get_room_messages(latest_room['id'])
    print(f"\n💬 メッセージ数: {len(messages)}")
    
    if messages:
        print("\n全メッセージ:")
        for i, msg in enumerate(messages, 1):
            if msg['role'] == 'user':
                print(f"\n  [{i}] 👤 ユーザー")
                print(f"      {msg['content']}")
            else:
                agent_name = msg.get('agent_name', '不明')
                icon = msg.get('icon', '❓')
                print(f"\n  [{i}] {icon} {agent_name}")
                print(f"      {msg['content']}")
    else:
        print("  メッセージがありません")
    
    # 4. 議事録
    board_content = json.loads(latest_room['board_content'])
    print(f"\n📋 議事録:")
    print(f"  合意事項: {len(board_content.get('agreements', []))}件")
    for item in board_content.get('agreements', []):
        print(f"    - {item}")
    print(f"  懸念点: {len(board_content.get('concerns', []))}件")
    for item in board_content.get('concerns', []):
        print(f"    - {item}")
else:
    print("\nルームが作成されていません")

print("\n" + "=" * 80)
