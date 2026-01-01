# AI Teams Standalone Version
# Generated automatically

# ==========================
# MODULE: database.py
# ==========================
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
                "model": "chatgpt-4o-latest",
                "provider": "openai",
                "system_default": 1
            },
            {
                "name": "📐 論理担当",
                "icon": "📐",
                "color": "#3b82f6",
                "role": "リスク管理の番人。「予算は？」「法律は？」「実現可能性は？」と常に疑う。数字とエビデンスを要求する。",
                "model": "chatgpt-4o-latest",
                "provider": "openai",
                "system_default": 1
            },
            {
                "name": "👽 アイデア",
                "icon": "👽",
                "color": "#10b981",
                "role": "空気を読まない天才。実現性は無視して、水平思考（ラテラルシンキング）で別角度のボールを投げる。",
                "model": "gemini-3-flash-preview",
                "provider": "google",
                "system_default": 1
            },
            {
                "name": "❤️ 共感担当",
                "icon": "❤️",
                "color": "#ec4899",
                "role": "ユーザーの代弁者。「それは便利だけど、ユーザーは疲れませんか？」「誰も傷つきませんか？」と感情面をケアする。",
                "model": "claude-sonnet-4-20250514",
                "provider": "anthropic",
                "system_default": 1
            },
            {
                "name": "📝 書記",
                "icon": "📝",
                "color": "#6b7280",
                "role": "透明な記録者。会話の文脈を読み解き、構造化する能力に特化。",
                "model": "claude-sonnet-4-20250514",
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


# ==========================
# MODULE: llm_client.py
# ==========================
"""
AI Teams - LLM Client Wrapper
各社APIの統一インターフェース（ストリーミング対応）
"""
import openai
import anthropic
import google.generativeai as genai
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')

from typing import List, Dict, Iterator, Optional

class LLMClient:
    """LLM APIの統一クライアント"""
    
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        
        # クライアントの初期化
        if api_keys.get("openai"):
            self.openai_client = openai.OpenAI(api_key=api_keys["openai"])
        if api_keys.get("google"):
            genai.configure(api_key=api_keys["google"])
        if api_keys.get("anthropic"):
            self.anthropic_client = anthropic.Anthropic(api_key=api_keys["anthropic"])
    
    def generate_stream(self, provider: str, model: str, messages: List[Dict]) -> Iterator[str]:
        """ストリーミング生成（統一インターフェース）"""
        if provider == "openai":
            yield from self._openai_stream(model, messages)
        elif provider == "google":
            yield from self._google_stream(model, messages)
        elif provider == "anthropic":
            yield from self._anthropic_stream(model, messages)
        else:
            yield f"[エラー: 不明なプロバイダー {provider}]"
    
    def _openai_stream(self, model: str, messages: List[Dict]) -> Iterator[str]:
        """OpenAI ストリーミング"""
        try:
            stream = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            yield f"[OpenAI エラー: {str(e)}]"
    
    def _google_stream(self, model: str, messages: List[Dict]) -> Iterator[str]:
        """Google Gemini ストリーミング"""
        try:
            model_instance = genai.GenerativeModel(model)
            
            # メッセージ形式を変換
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            
            response = model_instance.generate_content(
                prompt,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            yield f"[Gemini エラー: {str(e)}]"
    
    def _anthropic_stream(self, model: str, messages: List[Dict]) -> Iterator[str]:
        """Anthropic Claude ストリーミング"""
        try:
            # システムメッセージを分離
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
            user_messages = [m for m in messages if m["role"] != "system"]
            
            with self.anthropic_client.messages.stream(
                model=model,
                max_tokens=1500,
                system=system_msg,
                messages=user_messages
            ) as stream:
                for text in stream.text_stream:
                    yield text
        
        except Exception as e:
            yield f"[Claude エラー: {str(e)}]"
    
    def generate(self, provider: str, model: str, messages: List[Dict]) -> str:
        """非ストリーミング生成（後方互換性のため）"""
        result = ""
        for chunk in self.generate_stream(provider, model, messages):
            result += chunk
        return result


# ==========================
# MODULE: app.py
# ==========================
import streamlit as st
import time
import json
import re
import traceback
from datetime import datetime, timedelta

# ==========================================
# 設定 & CSS
# ==========================================
st.set_page_config(
    page_title="AI Teams: Professional",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# アクセシビリティ & UX向上CSS
st.markdown("""
<style>
    /* ボタンのタップ領域を拡張 */
    .stButton button {
        min-height: 44px; /* WCAG AAA基準 */
        margin-bottom: 8px;
        font-weight: bold;
    }
    /* エージェント名のスタイル */
    .agent-header {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .agent-name {
        font-weight: bold;
        font-size: 1.05em;
    }
    .agent-role {
        color: #9ca3af; /* アクセシビリティ改善: コントラスト比 5.8:1 */
        font-size: 0.85em;
        font-weight: normal;
    }
    /* 介入ボタンのスタイル調整 */
    div[data-testid="column"] > div > div > div > button {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# データベース & API
st.cache_resource.clear()
@st.cache_resource
def get_database():
    return Database()

db = get_database()

def load_api_keys():
    try:
        with open("API_KEY.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        return {
            "google": lines[1].strip() if len(lines) > 1 else "",
            "openai": lines[4].strip() if len(lines) > 4 else "",
            "anthropic": lines[7].strip() if len(lines) > 7 else ""
        }
    except:
        return db.get_api_keys()

api_keys = load_api_keys()
llm_client = LLMClient(api_keys)

if "current_room_id" not in st.session_state:
    st.session_state.current_room_id = None

# ==========================================
# 定数 & ヘルパー
# ==========================================
MODEL_OPTIONS = {
    "openai": ["chatgpt-4o-latest", "gpt-4-turbo", "gpt-3.5-turbo"],
    "google": ["gemini-1.5-pro", "gemini-1.5-flash"],
    "anthropic": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"]
}

def extract_json(text):
    try:
        return json.loads(text)
    except:
        pass
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match: return json.loads(match.group(1))
    match = re.search(r'\{[\s\S]*\}', text)
    if match: return json.loads(match.group(0))
    return None

# ==========================================
# エージェント管理モーダル
# ==========================================
@st.dialog("エージェント管理")
def manage_agents():
    tab_new, tab_edit = st.tabs(["➕ 新規作成", "📝 編集・削除"])
    
    with tab_new:
        st.subheader("新しいエージェントを作成")
        name = st.text_input("名前", placeholder="例: 論理担当", key="new_name")
        icon = st.text_input("アイコン (絵文字)", placeholder="📐", key="new_icon")
        role = st.text_area("役割プロンプト", placeholder="あなたは論理的な分析官です...", key="new_role")
        
        c1, c2 = st.columns(2)
        with c1:
            provider = st.selectbox("プロバイダー", ["openai", "google", "anthropic"], key="new_provider")
        with c2:
            models = MODEL_OPTIONS.get(provider, ["default"])
            model = st.selectbox("モデル", models, key="new_model")
        color = st.color_picker("イメージカラー", "#3b82f6", key="new_color")
        
        if st.button("作成", key="create_btn", type="primary"):
            if name and role:
                db.create_agent(name, icon, color, role, model, provider)
                st.success(f"{name} を作成しました")
                time.sleep(1)
                st.rerun()

    with tab_edit:
        agents = db.get_all_agents()
        target_id = st.selectbox("編集するエージェントを選択", 
                               options=[a['id'] for a in agents],
                               format_func=lambda x: next((f"{a['icon']} {a['name']}" for a in agents if a['id'] == x), "Unknown"),
                               key="edit_select")
        target = next((a for a in agents if a['id'] == target_id), None)
        
        if target:
            st.divider()
            e_name = st.text_input("名前", value=target['name'], key=f"e_name_{target_id}")
            e_role = st.text_area("役割", value=target['role'], height=150, key=f"e_role_{target_id}")
            e_provider = st.selectbox("プロバイダー", ["openai", "google", "anthropic"], 
                                    index=["openai","google","anthropic"].index(target['provider']) if target['provider'] in ["openai","google","anthropic"] else 0,
                                    key=f"e_prov_{target_id}")
            e_model = st.selectbox("モデル", MODEL_OPTIONS.get(e_provider, [target['model']]), key=f"e_mod_{target_id}")
            
            c1, c2 = st.columns([1,1])
            if c1.button("💾 保存", key=f"save_{target_id}"):
                db.update_agent(target_id, e_name, target['icon'], target['color'], e_role, e_model, e_provider)
                st.success("更新しました")
                time.sleep(1)
                st.rerun()
            if c2.button("🗑️ 削除", type="primary", key=f"del_{target_id}"):
                db.delete_agent(target_id)
                st.rerun()

# ==========================================
# サイドバー: ナビゲーション & 管理 (至高のUX構成)
# ==========================================
with st.sidebar:
    st.title("AI Teams 🧠")
    
    if st.button("🏠 ホーム", use_container_width=True, key="home_btn"):
        st.session_state.current_room_id = None
        st.rerun()
    
    # 新規作成ボタン (最上部・最大)
    # 新規作成ダイアログ & ボタン
    @st.dialog("＋ 新しい会議室を作成")
    def create_new_room_dialog():
        default_title = f"会議 {datetime.now().strftime('%m/%d %H:%M')}"
        title = st.text_input("会議名", value=default_title)
        
        all_agents = db.get_all_agents()
        # デフォルトエージェントを選択状態に
        default_ids = [a['id'] for a in all_agents if a.get('system_default')]
        
        agent_options = {a['id']: f"{a['icon']} {a['name']}" for a in all_agents}
        
        selected_ids = st.multiselect(
            "参加メンバー",
            options=list(agent_options.keys()),
            format_func=lambda x: agent_options[x],
            default=default_ids
        )
        
        first_prompt = st.text_area("最初の指示 (任意)", placeholder="例: 今期のマーケティング施策についてブレストしたい")
        
        if st.button("🚀 会議を開始", type="primary", use_container_width=True):
            # create_room(title, description, agent_ids)
            # descriptionをpromptとして保存
            new_id = db.create_room(title, first_prompt, selected_ids)
            
            if first_prompt:
                db.add_message(new_id, "user", first_prompt)
            
            st.session_state.current_room_id = new_id
            st.rerun()

    if st.button("＋ 新しい会議室", type="primary", use_container_width=True, key="sidebar_new_room_btn"):
        create_new_room_dialog()

    st.markdown("---")

    # --- 会議室マネージャー (一覧・一括削除) ---
    @st.dialog("🗂 会議室マネージャー", width="large")
    def open_room_manager():
        st.caption("過去の会議室を一覧で管理・削除できます。")
        all_rooms = db.get_all_rooms()
        
        if not all_rooms:
            st.info("会議室はまだありません。")
            return

        # データフレーム用のデータ作成
        df_data = []
        for r in all_rooms:
            df_data.append({
                "ID": r["id"],
                "delete": False,
                "title": r["title"],
                "created_at": r["created_at"][:16],
                "updated_at": r["updated_at"][:16] if r["updated_at"] else ""
            })

        # データエディタで表示
        edited_df = st.data_editor(
            df_data,
            column_config={
                "ID": None, 
                "delete": st.column_config.CheckboxColumn("削除", default=False),
                "title": st.column_config.TextColumn("会議名", width="medium", disabled=True), 
                "created_at": st.column_config.TextColumn("作成日時", width="small", disabled=True),
                "updated_at": st.column_config.TextColumn("最終更新", width="small", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key="room_manager_editor"
        )

        # 削除実行
        selected_rows = [row for row in edited_df if row["delete"]]
        if selected_rows:
            st.error(f"⚠️ {len(selected_rows)} 件の会議室を選択中")
            if st.button("選択した会議室を完全に削除", type="primary"):
                for row in selected_rows:
                    db.delete_room(row["ID"])
                    if st.session_state.current_room_id == row["ID"]:
                        st.session_state.current_room_id = None
                st.toast("✅ 削除しました")
                time.sleep(1)
                st.rerun()

    if st.button("� 履歴一覧・管理", use_container_width=True):
        open_room_manager()

    st.caption("📜 History")
    # All Rooms
    all_rooms = db.get_all_rooms()
    all_rooms.sort(key=lambda x: x['updated_at'] or x['created_at'], reverse=True)
    
    today = datetime.now().date()
    yesterday_date = today - timedelta(days=1)
    
    # グループ辞書 (挿入順序保持)
    history_groups = {
        "🌟 今日": [],
        "⏮️ 昨日": [],
        "🗓️ 過去7日間": [],
        "🗄️ 過去30日間": [],
        "📂 もっと前": []
    }
    
    for r in all_rooms:
        try:
            # 日付解析 (SQLiteの文字列フォーマット依存)
            ts_str = r.get('updated_at') or r['created_at']
            if not ts_str: continue
            
            # 簡易パース
            try:
                dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            except:
                dt = datetime.strptime(ts_str[:19], '%Y-%m-%d %H:%M:%S')
            
            r_date = dt.date()
            diff_days = (today - r_date).days
            
            if diff_days == 0:
                history_groups["🌟 今日"].append(r)
            elif diff_days == 1:
                history_groups["⏮️ 昨日"].append(r)
            elif diff_days <= 7:
                history_groups["🗓️ 過去7日間"].append(r)
            elif diff_days <= 30:
                history_groups["🗄️ 過去30日間"].append(r)
            else:
                history_groups["📂 もっと前"].append(r)
        except:
             history_groups["📂 もっと前"].append(r)

    # 描画
    for g_name, g_items in history_groups.items():
        if not g_items: continue
        
        # 今日だけデフォルト展開
        is_expanded = (g_name == "🌟 今日")
        
        with st.expander(f"{g_name} ({len(g_items)})", expanded=is_expanded):
            for r in g_items:
                label = r['title']
                if len(label) > 16: label = label[:15] + "…"
                
                # Active状態のデザイン
                b_type = "primary" if st.session_state.current_room_id == r['id'] else "secondary"
                
                if st.button(label, key=f"nav_{r['id']}", type=b_type, use_container_width=True):
                    st.session_state.current_room_id = r['id']
                    st.rerun()
            
    st.markdown("---")
    if st.button("👥 エージェント設定", use_container_width=True):
        manage_agents()
        
    auto_mode = st.toggle("自動進行モード", value=True)

    # ルーム内設定 (リネームのみ)
    if st.session_state.current_room_id:
        st.markdown("---")
        with st.expander("⚙️ 会議室の設定"):
            current_room = next((r for r in all_rooms if r['id'] == st.session_state.current_room_id), None)
            if current_room:
                new_title = st.text_input("会議室名", value=current_room['title'])
                if new_title != current_room['title']:
                    if st.button("名称を更新"):
                        db.update_room_title(current_room['id'], new_title)
                        st.session_state.current_room_id = current_room['id'] # Refresh state trigger
                        st.rerun()
                st.caption("※削除は「🗂 履歴一覧・管理」から行えます")

# ==========================================
# メイン: ダッシュボード (動的マクロボタン)
# ==========================================
def render_dashboard():
    st.title("👋 お帰りなさい、オーナー。")
    st.markdown("##### 🚀 クイック・アクション")
    
    # テンプレート管理ダイアログ
    @st.dialog("🛠️ ショートカット設定")
    def configure_template(tpl):
        new_name = st.text_input("ボタン名", value=tpl['name'])
        new_prompt = st.text_area("デフォルトの指示プロンプト", value=tpl.get('prompt',''), height=100)
        
        all_agents = db.get_all_agents()
        agent_options = {a['id']: f"{a['icon']} {a['name']}" for a in all_agents}
        
        default_ids = st.multiselect(
            "招集するメンバー",
            options=list(agent_options.keys()),
            format_func=lambda x: agent_options[x],
            default=tpl['default_agent_ids']
        )
        
        if st.button("設定を保存", type="primary"):
            db.update_template(tpl['id'], new_name, new_prompt, default_ids)
            st.toast("✅ 設定を更新しました")
            time.sleep(0.5)
            st.rerun()

    # テンプレート描画
    try:
        templates = db.get_templates()
    except Exception as e:
        # DBマイグレーションがまだの場合のエラー回避
        templates = []
        
    if not templates:
        st.info("DB初期化中... リロードしてください")
        # ここでリロードすると無限ループのリスクがあるので何もしない
    
    cols = st.columns(3)
    for i, tpl in enumerate(templates):
        with cols[i % 3]:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                
                # メイン起動ボタン
                if c1.button(f"{tpl['icon']} {tpl['name']}", key=f"launch_{tpl['id']}", use_container_width=True):
                    # Room作成
                    # Descriptionにもプロンプトを入れておく
                    new_id = db.create_room(tpl['name'], tpl['prompt'], tpl['default_agent_ids'])
                    
                    # 初期プロンプト投入
                    if tpl.get('prompt'):
                        db.add_message(new_id, "user", tpl['prompt'])
                    
                    st.session_state.current_room_id = new_id
                    st.rerun()
                
                # 設定ボタン
                if c2.button("⚙️", key=f"conf_{tpl['id']}", help="構成を編集"):
                    configure_template(tpl)

    st.markdown("#### 📂 最近のプロジェクト")
    recents = db.get_all_rooms()
    recents.sort(key=lambda x: x['updated_at'] or x['created_at'], reverse=True)
    
    for r in recents[:3]:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{r['title']}**")
            c1.caption(f"{r['created_at'][:10]} - {r['description'][:40]}..." if r['description'] else "説明なし")
            if c2.button("再開", key=f"resume_db_{r['id']}"):
                st.session_state.current_room_id = r['id']
                st.rerun()

# ==========================================
# メイン: ルーム機能 (Unified Fragment)
# ==========================================
def run_discussion(room_id, container, max_turns=1):
    room_agents = db.get_room_agents(room_id)
    if not room_agents: return
    
    # st.statusで進行可視化
    with st.status("💀 会議を進行中...", expanded=True) as status:
        turns_processed = 0
        while turns_processed < max_turns:
            msgs = db.get_room_messages(room_id)
            if len(msgs) >= 32: break
            
            # 次の話者決定(簡易)
            next_idx = len(msgs) % len(room_agents)
            next_agent = room_agents[next_idx]
            
            status.update(label=f"🎤 {next_agent['name']} が発言の準備中...", state="running")
            
            with container:
                # プレースホルダーでストリーミング風
                with st.chat_message("assistant", avatar=next_agent['icon']):
                    ph = st.empty()
                    ph.markdown(f":grey[{next_agent['name']} が思考中...]")
                    
                    try:
                        context = [{"role": ("user" if m['role']=="user" else "assistant"), "content": m['content']} for m in msgs[-10:]]
                        sys_prompt = f"あなたは{next_agent['name']}です。役割:{next_agent['role']}。50文字以内で簡潔に発言してください。"
                        
                        response = llm_client.generate(next_agent['provider'], next_agent['model'], [{"role":"system", "content":sys_prompt}] + context)
                        
                        # アクセシブルなHTML表示
                        role_html = f"<span class='agent-role'>({next_agent.get('role', '')[:10]}...)</span>"
                        ph.markdown(f"<div class='agent-header'><span class='agent-name'>{next_agent['name']}</span>{role_html}</div>\n\n{response}", unsafe_allow_html=True)
                        
                        db.add_message(room_id, "assistant", response, next_agent['id'])
                        turns_processed += 1
                        
                    except Exception as e:
                        ph.error(f"Error: {e}")
                        break
            
            if max_turns == 1: break
            time.sleep(1)
            
        status.update(label="✅ 発言完了", state="complete", expanded=False)

@st.fragment
def render_room_interface(room_id, auto_mode):
    col_chat, col_info = st.columns([2, 1.3]) # リキッドレイアウト調整
    
    # データを一括取得
    room = db.get_room(room_id)
    messages = db.get_room_messages(room_id)


    # --- 右カラム: ワークスペース ---
    with col_info:
        st.subheader(f"📊 ワークスペース")
        
        tab_min, tab_todo, tab_viz = st.tabs(["📝 議事録", "✅ ToDo", "📊 構造図"])
        
        with tab_min:
            if st.button("🔄 議事録を更新", use_container_width=True):
                with st.spinner("書記AIが執筆中..."):
                    try:
                        scribe = next((a for a in db.get_room_agents(room_id) if "書記" in a['name']), None)
                        if not scribe: scribe = db.get_room_agents(room_id)[0] 
                        
                        all_msgs = db.get_room_messages(room_id)
                        text = "\n".join([f"{m.get('agent_name','User')}: {m['content']}" for m in all_msgs])
                        
                        prompt = f"""議論ログからJSON議事録を作成せよ。Markdownコードは含めるな。
出力形式例:
{{
  "topic": "テーマ",
  "agreements": ["合意1"],
  "concerns": ["懸念1"],
  "next_actions": ["TODO1"]
}}
ログ:
{text}"""
                        res = llm_client.generate(scribe['provider'], scribe['model'], [{"role":"user", "content":prompt}])
                        new_content = extract_json(res)
                        if new_content:
                            db.update_room_board(room_id, new_content)
                            st.toast("議事録を更新しました")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"生成エラー: {e}")
            
            content = {}
            try: content = json.loads(room['board_content'])
            except: pass
            
            # Markdownとして表示 & コピー用
            md_text = f"## 議題: {content.get('topic','未定')}\n\n"
            if content.get('agreements'):
                md_text += "### ✅ 合意事項\n" + "\n".join([f"- {i}" for i in content['agreements']]) + "\n\n"
            if content.get('concerns'):
                md_text += "### ⚠️ 懸念点\n" + "\n".join([f"- {i}" for i in content['concerns']]) + "\n\n"
            if content.get('next_actions'):
                md_text += "### 🚀 Next Actions\n" + "\n".join([f"- {i}" for i in content['next_actions']])
            
            st.markdown(md_text)
            with st.expander("📋 コピー用Markdown"):
                st.code(md_text, language='markdown')
        
        with tab_todo:
            st.write("抽出されたタスク:")
            if content.get('next_actions'):
                for i, action in enumerate(content['next_actions']):
                    st.checkbox(action, key=f"todo_{room_id}_{i}")
            else:
                st.caption("タスクはまだありません")
                
        with tab_viz:
            st.caption("議論の構造化マップ (Beta)")
            st.graphviz_chart("""
            digraph {
              rankdir=LR;
              node [shape=box, style=filled, fillcolor="#f0f2f6"];
              "User" -> "Moderator" [label="提案"];
              "Moderator" -> "Logic" [label="指名"];
              "Logic" -> "Idea" [label="指摘"];
            }
            """) 

    # --- 左カラム: チャット & 神の介入 ---
    with col_chat:
        st.subheader(f"💬 {room['title']}")
        container = st.container(height=650)
        
        with container:
            if not messages:
                st.info("👋 ようこそ、オーナー。チームは待機しています。最初の議題を投げかけてください。")
            
            for msg in messages:
                with st.chat_message(msg['role'], avatar=msg.get('icon')):
                    r_name = msg.get('agent_role', 'Participant')
                    if not r_name: r_name = "User" if msg['role'] == "user" else "AI"
                    
                    st.markdown(f"<div class='agent-header'><span class='agent-name'>{msg.get('agent_name', 'User')}</span><span class='agent-role'>({r_name[:15]}...)</span></div>", unsafe_allow_html=True)
                    st.write(msg['content'])
                    
                    # 引用アクションボタン (AIの発言のみ、かつ最新のいくつかの発言に対して)
                    if msg['role'] != 'user':
                        c1, c2, _ = st.columns([1, 1, 10])
                        # 画面がボタンだらけにならないよう、スタイリッシュに。
                        if c1.button("�", key=f"deep_{msg['id']}", help="この発言を深掘りさせる"):
                             db.add_message(room_id, "user", f"@{msg.get('agent_name')}さん、今の「{msg['content'][:20]}...」という点について、もっと具体的に説明してください。")
                             st.rerun()
                        if c2.button("🔥", key=f"crit_{msg['id']}", help="この発言に反論させる"):
                             db.add_message(room_id, "user", f"@{msg.get('agent_name')}さんの意見に対して、リスクや反論を挙げてください。")
                             st.rerun()
        
        # クイック介入ボタン群 (旧: 神の介入。全体の入力欄の上に配置)
        c_int = st.columns([1, 1, 1, 4])
        if c_int[0].button("� ストップ", help="議論を打ち切りまとめさせる"):
            db.add_message(room_id, "user", "一旦議論をストップ。ここまでの内容をまとめてください。")
            st.rerun()
        if c_int[1].button("🤔 論点整理", help="論点を整理させる"):
            db.add_message(room_id, "user", "今、何について議論しているか、論点を整理してください。")
            st.rerun()
        
        # 入力欄
        prompt = st.chat_input("チームに指示、または議題を入力...", key=f"chat_{room_id}")
        if prompt:
            db.add_message(room_id, "user", prompt)
            st.rerun()

        # 自動進行ロジック
        last_role = messages[-1]['role'] if messages else 'system'
        if last_role == 'user':
            run_discussion(room_id, container, max_turns=(16 if auto_mode else 1))
            st.rerun()
        elif auto_mode and last_role == 'assistant' and len(messages) < 32:
            run_discussion(room_id, container, max_turns=16)
            st.rerun()

# ==========================================
# APP ROUTING
# ==========================================
if st.session_state.current_room_id:
    render_room_interface(st.session_state.current_room_id, auto_mode)
else:
    render_dashboard()
