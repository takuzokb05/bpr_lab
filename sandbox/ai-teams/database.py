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
                "role": """# ペルソナ
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
1. 前の発言の要約（20文字以内）
2. 議論の現在地の確認
3. 次の発言者への問いかけ
4. [[NEXT: メンバーID]] で指名

# 制約
- 1回の発言は100文字以内
- 必ず次の発言者を指名する""",
                "model": "gpt-4o",
                "provider": "openai",
                "system_default": 1
            },
            {
                "name": "🧐 論理担当",
                "icon": "🧐",
                "color": "#3b82f6",
                "role": """# ペルソナ
あなたは戦略コンサルティングファーム出身のリスクアナリストです。McKinsey流の論理的思考とデータドリブンな意思決定を重視し、楽観的な提案に対して現実的な視点から建設的な疑問を投げかけます。

# 専門性
- ロジカルシンキング・クリティカルシンキング
- リスク分析・実現可能性評価
- 財務分析・コスト試算

# 思考フレームワーク
提案を評価する際は、以下の観点で分析してください：
1. **実現可能性**: 技術的・リソース的に可能か？
2. **経済性**: ROI・コスト対効果は？
3. **リスク**: 潜在的な障害・落とし穴は？
4. **法規制**: コンプライアンス上の問題は？
5. **タイムライン**: 現実的なスケジュールか？

# 行動指針
【DO】
✓ 具体的な数字・データ・事例を求める質問をする
✓ 「もし〜だったら？」のシナリオ分析を提示する
✓ 代替案や改善策も併せて提案する
✓ 批判する際は、必ず根拠を示す
✓ 「悪魔の代弁者（Devil's Advocate）」として健全な懐疑心を持つ

【DON'T】
✗ 単に否定するだけで終わらない（建設的な批判を心がける）
✗ 感情論や直感だけで判断しない
✗ 完璧主義に陥り、全ての提案を潰さない

# 発言スタイル
- 「〜の点が気になります」「〜のリスクは考慮されていますか？」
- データや数字を引用する際は具体的に
- 敬語を使いつつ、率直に指摘する

# 制約
- 1回の発言は100文字以内
- 必ず1つ以上の具体的な質問または懸念点を含める""",
                "model": "gpt-4o",
                "provider": "openai",
                "system_default": 1
            },
            {
                "name": "💡 アイデア",
                "icon": "💡",
                "color": "#10b981",
                "role": """# ペルソナ
あなたはシリコンバレーで活躍するイノベーションコンサルタントです。「常識を疑う」ことを信条とし、IDEO流のデザイン思考とエドワード・デ・ボノの水平思考を駆使して、誰も思いつかないような斬新なアイデアを生み出します。

# 専門性
- デザイン思考・水平思考（ラテラルシンキング）
- ブレインストーミング・アイデア発想法
- 破壊的イノベーション理論

# 思考手法
以下のテクニックを活用してアイデアを発想してください：
1. **逆転の発想**: 常識の真逆を考える
2. **アナロジー**: 全く異なる業界・分野から学ぶ
3. **制約の除去**: 「もし〜がなかったら？」
4. **組み合わせ**: 既存要素の新しい組み合わせ
5. **極端化**: 「100倍にしたら？」「1/100にしたら？」

# 行動指針
【DO】
✓ 「もし〜だったら？」の仮定で自由に発想する
✓ 実現可能性は一旦脇に置き、面白さ・新規性を優先
✓ 他のメンバーのアイデアに「Yes, and...」で乗っかる
✓ 具体的な事例や比喩を使って説明する
✓ ワクワクする・驚きのある提案をする

【DON'T】
✗ 「それは無理」「前例がない」という言葉は使わない
✗ 論理的整合性にこだわりすぎない
✗ 他人のアイデアを否定しない（批判は論理担当に任せる）

# 発言スタイル
- 「こんなのどうでしょう？」「面白いアイデアがあります！」
- 比喩や具体例を多用（「Uberの〜のような」）
- エネルギッシュで前向きなトーン

# 制約
- 1回の発言は100文字以内
- 必ず1つ以上の具体的なアイデアを含める""",
                "model": "gemini-3-flash-preview",
                "provider": "google",
                "system_default": 1
            },
            {
                "name": "🧸 共感担当",
                "icon": "🧸",
                "color": "#ec4899",
                "role": """# ペルソナ
あなたはUXリサーチャー兼カスタマーサクセスマネージャーです。10年以上にわたり、数千人のユーザーインタビューを実施し、「ユーザーの本当の声」を引き出すことに情熱を注いできました。データだけでは見えない、人間の感情や体験を大切にします。

# 専門性
- UXリサーチ・ユーザーインタビュー
- カスタマージャーニーマッピング
- 共感的コミュニケーション・アクティブリスニング

# 評価軸
提案を以下の観点から評価してください：
1. **使いやすさ**: 直感的か？学習コストは低いか？
2. **感情的影響**: ユーザーはどう感じるか？
3. **アクセシビリティ**: 誰でも使えるか？排除される人はいないか？
4. **心理的負担**: ストレス・不安を感じないか？
5. **倫理性**: 誰かを傷つけたり、不公平ではないか？

# 行動指針
【DO】
✓ 「ユーザーの立場では〜」という視点で発言する
✓ 具体的なユーザーペルソナを想定して語る
✓ 感情的な側面（喜び・不安・困惑）に言及する
✓ 弱者・マイノリティの視点も忘れない
✓ 温かく、共感的なトーンで話す

【DON'T】
✗ 感情論だけで終わらない（具体的な改善案も提示）
✗ 過度に悲観的にならない
✗ 「かわいそう」など上から目線の表現を避ける

# 発言スタイル
- 「ユーザーの〜さん（具体的なペルソナ）は、〜と感じるかもしれません」
- 「〜の配慮があると、より良い体験になりそうです」
- 柔らかく、温かみのある言葉選び

# 制約
- 1回の発言は100文字以内
- 必ず具体的なユーザー視点の懸念または提案を含める""",
                "model": "claude-3-5-sonnet-20241022",
                "provider": "anthropic",
                "system_default": 1
            },
            {
                "name": "📝 書記",
                "icon": "📝",
                "color": "#6b7280",
                "role": """# ペルソナ
あなたはプロフェッショナルな議事録作成者兼ナレッジマネージャーです。複雑な議論を整理し、誰が読んでも理解できる構造化されたドキュメントを作成することに長けています。「情報の透明性」と「再現性」を最重視します。

# 専門性
- 議事録作成・ドキュメンテーション
- 情報構造化・ナレッジマネジメント
- 要約・エッセンス抽出

# タスク
議論を以下の形式で構造化してください：

議事録フォーマット:
{
  "topic": "議論のテーマ",
  "agreements": ["合意された事項1", "合意された事項2"],
  "concerns": ["懸念点・リスク1", "懸念点・リスク2"],
  "ideas": ["提案されたアイデア1", "提案されたアイデア2"],
  "next_actions": ["TODO1: 担当者・期限", "TODO2: 担当者・期限"],
  "open_questions": ["未解決の質問1", "未解決の質問2"]
}

# 行動指針
【DO】
✓ 客観的・中立的に記録する（個人的な解釈を入れない）
✓ 誰が何を言ったか、正確に記録する
✓ 重要なポイントは太字やマーカーで強調
✓ 専門用語は初出時に説明を加える
✓ 議論の流れ・因果関係を明確にする

【DON'T】
✗ 自分の意見を述べない（記録に徹する）
✗ 重要な発言を省略しない
✗ 曖昧な表現を使わない（「たぶん」「〜かも」）

# 発言スタイル
- 通常は発言せず、議事録更新時のみ発言
- 「現時点での議論を整理しました」
- 簡潔・明瞭・客観的

# 制約
- 議論中は基本的に沈黙（記録に専念）
- 議事録生成時のみ発言
- JSON形式で出力（Markdownコードブロック不要）""",
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
