"""
AI Teams - Database Management
SQLiteを使用したデータ永続化層
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib

class Database:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = "ai_teams.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式で取得
        return conn
    
    def init_database(self):
        """データベースとテーブルを初期化"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 設定テーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # エージェントテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            color TEXT NOT NULL,
            role TEXT NOT NULL,
            model TEXT NOT NULL,
            provider TEXT NOT NULL,
            system_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # ルームテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            board_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # メッセージテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            agent_id INTEGER,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
        """)
        
        # ルーム-エージェント関連テーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_agents (
            room_id INTEGER NOT NULL,
            agent_id INTEGER NOT NULL,
            PRIMARY KEY (room_id, agent_id),
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
        """)
        
        conn.commit()
        conn.close()
        
        # デフォルトエージェントを作成
        self.create_default_agents()
    
    def create_default_agents(self):
        """デフォルトエージェントを作成（初回のみ）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 既存のデフォルトエージェントをチェック
        cursor.execute("SELECT COUNT(*) FROM agents WHERE system_default = 1")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        default_agents = [
            {
                "name": "🎤 AIモデレーター",
                "icon": "🎤",
                "color": "#8b5cf6",
                "role": "知的で冷静な女性ニュースキャスター。物腰は柔らかいが進行管理は鉄壁。丁寧語で話し、各発言を要約してから次の発言者を指名する。",
                "model": "gpt-4o",
                "provider": "openai",
                "system_default": 1
            },
            {
                "name": "🧐 論理担当",
                "icon": "🧐",
                "color": "#3b82f6",
                "role": "リスク管理の番人。「予算は？」「法律は？」「実現可能性は？」と常に疑う。数字とエビデンスを要求する。",
                "model": "gpt-4o",
                "provider": "openai",
                "system_default": 1
            },
            {
                "name": "💡 アイデア",
                "icon": "💡",
                "color": "#10b981",
                "role": "空気を読まない天才。実現性は無視して、水平思考（ラテラルシンキング）で別角度のボールを投げる。",
                "model": "gemini-3-flash-preview",
                "provider": "google",
                "system_default": 1
            },
            {
                "name": "🧸 共感担当",
                "icon": "🧸",
                "color": "#ec4899",
                "role": "ユーザーの代弁者。「それは便利だけど、ユーザーは疲れませんか？」「誰も傷つきませんか？」と感情面をケアする。",
                "model": "claude-3-5-sonnet-20241022",
                "provider": "anthropic",
                "system_default": 1
            },
            {
                "name": "📝 書記",
                "icon": "📝",
                "color": "#6b7280",
                "role": "透明な記録者。会話の文脈を読み解き、構造化する能力に特化。",
                "model": "claude-3-5-sonnet-20241022",
                "provider": "anthropic",
                "system_default": 1
            }
        ]
        
        for agent in default_agents:
            cursor.execute("""
            INSERT INTO agents (name, icon, color, role, model, provider, system_default)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (agent["name"], agent["icon"], agent["color"], agent["role"], 
                  agent["model"], agent["provider"], agent["system_default"]))
        
        conn.commit()
        
        # テンプレートテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '🚀',
            prompt TEXT,
            default_agent_ids TEXT
        )
        """)
        
        # 初期テンプレート
        cursor.execute("SELECT count(*) FROM templates")
        if cursor.fetchone()[0] == 0:
            defaults = [
                ("💡 新規事業ブレスト", "🚀", "革新的なビジネスアイデアを3つ提案し、それぞれの収益性を議論してください。", "[2, 3]"), 
                ("🐛 バグ原因究明", "🛠️", "発生しているシステム障害の原因と解決策を論理的に分析してください。", "[2, 4]"),
                ("🔮 将来戦略会議", "📈", "3年後の市場環境を予測し、我々が取るべき戦略を議論してください。", "[1, 2, 3]")
            ]
            cursor.executemany("INSERT INTO templates (name, icon, prompt, default_agent_ids) VALUES (?, ?, ?, ?)", defaults)
            conn.commit()
        conn.close()
    
    # ========== 設定管理 ==========
    
    def save_setting(self, key: str, value: str):
        """設定を保存"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        conn.commit()
        conn.close()
    
    def get_setting(self, key: str) -> Optional[str]:
        """設定を取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result["value"] if result else None
    
    def get_api_keys(self) -> Dict[str, str]:
        """全APIキーを取得"""
        return {
            "openai": self.get_setting("api_key_openai") or "",
            "google": self.get_setting("api_key_google") or "",
            "anthropic": self.get_setting("api_key_anthropic") or ""
        }
    
    def save_api_keys(self, openai: str = None, google: str = None, anthropic: str = None):
        """APIキーを保存"""
        if openai:
            self.save_setting("api_key_openai", openai)
        if google:
            self.save_setting("api_key_google", google)
        if anthropic:
            self.save_setting("api_key_anthropic", anthropic)
    
    # ========== エージェント管理 ==========
    
    def get_all_agents(self) -> List[Dict]:
        """全エージェントを取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agents ORDER BY system_default DESC, id ASC")
        agents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return agents
    
    def get_agent(self, agent_id: int) -> Optional[Dict]:
        """特定のエージェントを取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    def create_agent(self, name: str, icon: str, color: str, role: str, 
                    model: str, provider: str) -> int:
        """新しいエージェントを作成"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO agents (name, icon, color, role, model, provider, system_default)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (name, icon, color, role, model, provider))
        agent_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return agent_id
    
    def update_agent(self, agent_id: int, name: str, icon: str, color: str, 
                    role: str, model: str, provider: str):
        """エージェントを更新"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE agents 
        SET name = ?, icon = ?, color = ?, role = ?, model = ?, provider = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (name, icon, color, role, model, provider, agent_id))
        conn.commit()
        conn.close()
    
    def delete_agent(self, agent_id: int):
        """エージェントを削除"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        conn.commit()
        conn.close()
    
    # ========== ルーム管理 ==========
    
    def create_room(self, title: str, description: str = "", agent_ids: List[int] = None) -> int:
        """新しいルームを作成"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ルーム作成
        cursor.execute("""
        INSERT INTO rooms (title, description, board_content)
        VALUES (?, ?, ?)
        """, (title, description, json.dumps({"topic": title, "agreements": [], "concerns": [], "next_actions": []})))
        room_id = cursor.lastrowid
        
        # エージェントを関連付け
        if agent_ids:
            for agent_id in agent_ids:
                cursor.execute("""
                INSERT INTO room_agents (room_id, agent_id)
                VALUES (?, ?)
                """, (room_id, agent_id))
        
        conn.commit()
        conn.close()
        return room_id
    
    def get_all_rooms(self) -> List[Dict]:
        """全ルームを取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms ORDER BY updated_at DESC")
        rooms = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rooms
    
    def get_room(self, room_id: int) -> Optional[Dict]:
        """特定のルームを取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    def update_room_title(self, room_id: int, new_title: str):
        """ルーム名を変更"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE rooms SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_title, room_id))
        conn.commit()
        conn.close()
    
    def update_room_board(self, room_id: int, board_content: Dict):
        """ルームの議事録を更新"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE rooms 
        SET board_content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (json.dumps(board_content, ensure_ascii=False), room_id))
        conn.commit()
        conn.close()
    
    def delete_room(self, room_id: int):
        """ルームとその関連データを削除"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 関連データの削除
        cursor.execute("DELETE FROM room_agents WHERE room_id = ?", (room_id,))
        cursor.execute("DELETE FROM messages WHERE room_id = ?", (room_id,))
        
        # ルームの削除
        cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        
        conn.commit()
        conn.close()
    
    def get_room_agents(self, room_id: int) -> List[Dict]:
        """ルームに参加しているエージェントを取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.* FROM agents a
        JOIN room_agents ra ON a.id = ra.agent_id
        WHERE ra.room_id = ?
        """, (room_id,))
        agents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return agents
    
    # ========== メッセージ管理 ==========
    
    def add_message(self, room_id: int, role: str, content: str, agent_id: int = None):
        """メッセージを追加"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO messages (room_id, role, agent_id, content)
        VALUES (?, ?, ?, ?)
        """, (room_id, role, agent_id, content))
        
        # ルームの更新日時を更新
        cursor.execute("""
        UPDATE rooms SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (room_id,))
        
        conn.commit()
        conn.close()
    
    def get_room_messages(self, room_id: int) -> List[Dict]:
        """ルームのメッセージを取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT m.*, a.name as agent_name, a.icon, a.color, a.role as agent_role
        FROM messages m
        LEFT JOIN agents a ON m.agent_id = a.id
        WHERE m.room_id = ?
        ORDER BY m.created_at ASC
        """, (room_id,))
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages

    # --- テンプレート操作メソッド ---
    def get_templates(self) -> List[Dict]:
        """全テンプレートを取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM templates")
            templates = []
            for row in cursor.fetchall():
                d = dict(row)
                try:
                    d['default_agent_ids'] = json.loads(d['default_agent_ids']) if d['default_agent_ids'] else []
                except:
                    d['default_agent_ids'] = []
                templates.append(d)
        except:
             templates = []
        conn.close()
        return templates

    def update_template(self, template_id, name, prompt, agent_ids):
        """テンプレートを更新"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE templates 
            SET name = ?, prompt = ?, default_agent_ids = ?
            WHERE id = ?
        """, (name, prompt, json.dumps(agent_ids), template_id))
        conn.commit()
        conn.close()

    def get_room_agent_ids(self, room_id: int) -> List[int]:
        """現在の参加エージェントIDリストを取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT agent_id FROM room_agents WHERE room_id = ?", (room_id,))
        ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return ids

    def update_room_agents_diff(self, room_id: int, new_agent_ids: List[int]):
        """差分更新し、入退室ログを返す"""
        old_ids = set(self.get_room_agent_ids(room_id))
        new_ids = set(new_agent_ids)
        
        added = new_ids - old_ids
        removed = old_ids - new_ids
        
        if not added and not removed:
            return None 

        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 削除
            if removed:
                ph = ','.join(['?'] * len(removed))
                cursor.execute(f"DELETE FROM room_agents WHERE room_id = ? AND agent_id IN ({ph})", (room_id, *removed))
            # 追加
            if added:
                cursor.executemany("INSERT INTO room_agents (room_id, agent_id) VALUES (?, ?)", 
                                   [(room_id, aid) for aid in added])
            
            conn.commit()
            
            # ログメッセージ作成
            log_messages = []
            if added:
                ph = ','.join(['?'] * len(added))
                cursor.execute(f"SELECT name FROM agents WHERE id IN ({ph})", list(added))
                names = [r[0] for r in cursor.fetchall()]
                log_messages.append(f"🟢 {', '.join(names)} が入室しました。")
            
            if removed:
                ph = ','.join(['?'] * len(removed))
                cursor.execute(f"SELECT name FROM agents WHERE id IN ({ph})", list(removed))
                names = [r[0] for r in cursor.fetchall()]
                # 退室メッセージはシンプルに
                # log_messages.append(f"🔴 {', '.join(names)} が退室しました。")
                pass # 退室ログはウルサイので出さないか、オプションにする。今回は提案通り出すならコメントアウト解除。
                     # 提案では「記録として残す」重要性があったので出す。
                log_messages.append(f"🔴 {', '.join(names)} が退室しました。")
                
            return "\n".join(log_messages)

        finally:
            conn.close()

    def edit_message_and_truncate(self, room_id: int, message_id: int, new_content: str):
        """メッセージを編集し、それ以降の未来を全て削除する（死に戻り）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 1. 対象メッセージの更新
            cursor.execute("UPDATE messages SET content = ? WHERE id = ?", (new_content, message_id))
            
            # 2. そのメッセージより「後（未来）」のメッセージを削除
            cursor.execute("DELETE FROM messages WHERE room_id = ? AND id > ?", (room_id, message_id))
            
            # 3. ルームの更新日時更新
            cursor.execute("UPDATE rooms SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (room_id,))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
