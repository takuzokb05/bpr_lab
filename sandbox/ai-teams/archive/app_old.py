"""
AI Teams - Main Application
プロフェッショナルな討論番組スタイルのAIチャットアプリ
"""
import streamlit as st
import time
from datetime import datetime
from database import Database
from llm_client import LLMClient
import json

# ページ設定
st.set_page_config(
    page_title="AI Teams - AI討論チャット",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# データベース初期化
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# セッション状態の初期化
if "current_room_id" not in st.session_state:
    st.session_state.current_room_id = None
if "discussion_running" not in st.session_state:
    st.session_state.discussion_running = False
if "phase" not in st.session_state:
    st.session_state.phase = "opening"
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0

# APIキーの取得（API_KEY.txtから直接読み込み）
try:
    with open("API_KEY.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    api_keys = {
        "google": lines[1].strip() if len(lines) > 1 else "",
        "openai": lines[4].strip() if len(lines) > 4 else "",
        "anthropic": lines[7].strip() if len(lines) > 7 else ""
    }
except FileNotFoundError:
    # API_KEY.txtがない場合はDBから取得
    api_keys = db.get_api_keys()

# APIキーが未設定の場合は設定画面を表示
if not any(api_keys.values()):
    st.title("🔑 初期設定")
    st.markdown("### APIキーを設定してください")
    st.markdown("API_KEY.txtファイルを作成するか、ここで入力してください。")
    
    with st.form("api_keys_form"):
        openai_key = st.text_input("OpenAI API Key", type="password")
        google_key = st.text_input("Google API Key", type="password")
        anthropic_key = st.text_input("Anthropic API Key", type="password")
        
        submitted = st.form_submit_button("保存して開始")
        if submitted:
            db.save_api_keys(openai_key, google_key, anthropic_key)
            st.success("✅ APIキーを保存しました!")
            st.rerun()
    
    st.stop()

# LLMクライアント初期化
llm_client = LLMClient(api_keys)

# カスタムCSS
st.markdown("""
<style>
    /* Slack/Teamsライクなデザイン */
    .main {
        background-color: #0e1117;
    }
    
    /* サイドバー */
    .css-1d391kg {
        background-color: #1a1d24;
    }
    
    /* メッセージバブル */
    .message-bubble {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        border-left: 4px solid;
        animation: fadeIn 0.5s ease-in;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        color: #ffffff;  /* 白色のテキスト */
    }
    
    .message-bubble .agent-name {
        font-weight: bold;
        margin-bottom: 8px;
        color: #e2e8f0;  /* 明るいグレー */
    }
    
    .message-bubble .message-content {
        color: #f7fafc;  /* ほぼ白 */
        line-height: 1.6;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* ルームリスト */
    .room-item {
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        background: #2d3748;
    }
    
    .room-item:hover {
        background: #3d4758;
        transform: translateX(4px);
    }
    
    .room-item.active {
        background: #4a5568;
        border-left: 4px solid #8b5cf6;
    }
</style>
""", unsafe_allow_html=True)

# ========== 議論の自動進行（メイン処理の前に実行） ==========
if st.session_state.discussion_running and st.session_state.current_room_id:
    try:
        turn_count = st.session_state.turn_count
        phase = st.session_state.phase
        
        # ルームのエージェントを取得
        room_agents = db.get_room_agents(st.session_state.current_room_id)
        
        if not room_agents:
            st.error("エージェントが選択されていません")
            st.session_state.discussion_running = False
            st.stop()
        
        # 次の発言者を決定
        next_agent = None
        
        # フェーズ遷移の管理
        if turn_count == 0:
            st.session_state.phase = "opening"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn_count == 1:
            st.session_state.phase = "divergence"
            idea_agent = next((a for a in room_agents if "アイデア" in a['name']), None)
            next_agent = idea_agent if idea_agent else room_agents[1 % len(room_agents)]
        elif turn_count <= 6:
            next_agent = room_agents[turn_count % len(room_agents)]
        elif turn_count == 7:
            st.session_state.phase = "convergence"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn_count <= 12:
            next_agent = room_agents[turn_count % len(room_agents)]
        elif turn_count == 13:
            st.session_state.phase = "conclusion"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn_count < 16:
            next_agent = room_agents[0]
        else:
            # 16ターン以降 - 議論は終了したが、追加質問があれば議事録を更新
            st.session_state.discussion_running = False
            next_agent = None
        
        # 議論が終了したら（16ターン以降）、書記AIに議事録を作成させる
        if turn_count >= 16 and not st.session_state.discussion_running:
            # 書記エージェントを探す
            scribe = next((a for a in room_agents if "書記" in a['name']), None)
            
            if scribe:
                # 全メッセージを取得
                all_messages = db.get_room_messages(st.session_state.current_room_id)
                
                # 議論内容を整形
                discussion_text = "\n\n".join([
                    f"[{msg.get('agent_name', 'ユーザー')}]: {msg['content']}"
                    for msg in all_messages
                ])
                
                # 書記AIに議事録作成を依頼
                scribe_prompt = f"""以下の議論を分析し、構造化された議事録を作成してください。

【議論内容】
{discussion_text}

【出力形式】
以下のJSON形式で出力してください:
{{
  "topic": "議論のテーマ",
  "agreements": ["合意事項1", "合意事項2", ...],
  "concerns": ["懸念点1", "懸念点2", ...],
  "next_actions": ["アクション1", "アクション2", ...]
}}

重要: 必ずJSON形式で出力してください。"""
                
                scribe_context = [{"role": "user", "content": scribe_prompt}]
                scribe_system = f"""あなたは{scribe['name']}です。
役割: {scribe['role']}

議論を客観的に分析し、重要なポイントを抽出してください。
必ずJSON形式で出力してください。"""
                
                try:
                    scribe_response = llm_client.generate(
                        scribe['provider'],
                        scribe['model'],
                        [{"role": "system", "content": scribe_system}] + scribe_context
                    )
                    
                    # JSONを抽出
                    import re
                    json_match = re.search(r'\{.*\}', scribe_response, re.DOTALL)
                    if json_match:
                        board_content = json.loads(json_match.group())
                        db.update_room_board(st.session_state.current_room_id, board_content)
                except Exception as e:
                    st.warning(f"議事録の自動生成に失敗しました: {str(e)}")
        
        # エージェントの応答を生成
        if next_agent and st.session_state.discussion_running:
            # 最近のメッセージを取得
            messages = db.get_room_messages(st.session_state.current_room_id)
            recent_messages = messages[-5:] if len(messages) > 5 else messages
            
            # コンテキストを準備
            context = []
            for msg in recent_messages:
                if msg['role'] == 'user':
                    context.append({"role": "user", "content": msg['content']})
                else:
                    context.append({"role": "assistant", "content": msg['content']})
            
            # システムプロンプトを生成
            if "モデレーター" in next_agent['name'] or "司会" in next_agent['name']:
                # 司会者専用プロンプト
                system_prompt = f"""あなたは{next_agent['name']}です。
役割: {next_agent['role']}

現在のフェーズ: {phase}

【重要】あなたは司会者です。自分で答えを出してはいけません。
- 議論を整理し、次の発言者を指名することだけに専念してください
- 「なるほど、〇〇という意見ですね。では、△△担当さん、いかがでしょうか?」のように進行してください
- 自分でメニューを考えたり、具体的な提案をしてはいけません

必ず日本語で、丁寧語（です・ます調）で話してください。
簡潔に（50文字以内）。"""
            else:
                # 他のエージェント用プロンプト
                system_prompt = f"""あなたは{next_agent['name']}です。
役割: {next_agent['role']}

現在のフェーズ: {phase}

必ず日本語で思考し、発言してください。
あなたの性格と役割に忠実に、議論に貢献してください。
詳細に、具体的に説明してください。"""
            
            # LLMに問い合わせ
            full_context = [{"role": "system", "content": system_prompt}] + context
            
            response = llm_client.generate(
                next_agent['provider'],
                next_agent['model'],
                full_context
            )
            
            # メッセージを保存
            db.add_message(
                st.session_state.current_room_id,
                "assistant",
                response,
                next_agent['id']
            )
            
            
            # ターン数を増やす
            st.session_state.turn_count += 1
            
            time.sleep(2)  # メッセージを読む時間を確保
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ エラー: {str(e)}")
        st.session_state.discussion_running = False

# ========== サイドバー ==========
with st.sidebar:
    st.title("🎤 AI Teams")
    
    # 新規会議ボタン
    if st.button("➕ 新規会議", use_container_width=True, type="primary"):
        st.session_state.show_new_room_dialog = True
    
    st.markdown("---")
    
    # 会議リスト
    st.markdown("### 📂 過去の会議")
    rooms = db.get_all_rooms()
    
    if rooms:
        for room in rooms:
            is_active = st.session_state.current_room_id == room["id"]
            if st.button(
                f"{'🔵 ' if is_active else '⚪ '}{room['title'][:20]}...",
                key=f"room_{room['id']}",
                use_container_width=True
            ):
                st.session_state.current_room_id = room["id"]
                st.session_state.discussion_running = False
                st.rerun()
    else:
        st.info("まだ会議がありません")
    
    st.markdown("---")
    
    # 設定メニュー
    with st.expander("⚙️ エージェント管理"):
        if st.button("エージェント一覧・編集", use_container_width=True):
            st.session_state.show_agent_management = True
    
    with st.expander("🔧 API設定"):
        if st.button("APIキーを再設定", use_container_width=True):
            st.session_state.show_api_settings = True


# エージェント管理画面
if st.session_state.get("show_agent_management", False):
    st.title("⚙️ エージェント管理")
    
    agents = db.get_all_agents()
    
    st.markdown("### 登録済みエージェント")
    for agent in agents:
        with st.expander(f"{agent['icon']} {agent['name']}", expanded=False):
            st.markdown(f"**役割:** {agent['role']}")
            st.markdown(f"**モデル:** {agent['model']} ({agent['provider']})")
            st.markdown(f"**カラー:** {agent['color']}")
            if agent['system_default'] == 1:
                st.info("🔒 システムデフォルトエージェント（削除不可）")
            else:
                if st.button(f"削除", key=f"delete_{agent['id']}"):
                    db.delete_agent(agent['id'])
                    st.success(f"✅ {agent['name']}を削除しました")
                    time.sleep(1)
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### 新しいエージェントを追加")
    
    with st.form("new_agent_form"):
        new_name = st.text_input("名前", placeholder="例: 🔥 毒舌エンジニア")
        new_icon = st.text_input("アイコン（絵文字）", placeholder="例: 🔥")
        new_color = st.color_picker("カラー", "#ff6b6b")
        new_role = st.text_area("役割・性格", placeholder="例: 関西弁で毒舌。技術的な矛盾を容赦なく指摘する。")
        new_provider = st.selectbox("プロバイダー", ["openai", "google", "anthropic"])
        
        if new_provider == "openai":
            new_model = st.selectbox("モデル", ["chatgpt-4o-latest", "gpt-4o", "o1-preview"])
        elif new_provider == "google":
            new_model = st.selectbox("モデル", ["gemini-3-flash-preview", "gemini-1.5-pro", "gemini-1.5-flash"])
        else:
            new_model = st.selectbox("モデル", ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("キャンセル", use_container_width=True):
                st.session_state.show_agent_management = False
                st.rerun()
        with col2:
            if st.form_submit_button("追加", use_container_width=True, type="primary"):
                if new_name and new_icon and new_role:
                    db.create_agent(new_name, new_icon, new_color, new_role, new_model, new_provider)
                    st.success(f"✅ {new_name}を追加しました!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("全ての項目を入力してください")

# API設定画面
elif st.session_state.get("show_api_settings", False):
    st.title("🔧 API設定")
    
    current_keys = db.get_api_keys()
    
    with st.form("api_settings_form"):
        st.markdown("### APIキーを再設定")
        st.info("空欄のままにすると、現在の設定が保持されます")
        
        openai_key = st.text_input(
            "OpenAI API Key", 
            value="*" * 20 if current_keys["openai"] else "",
            type="password",
            placeholder="新しいキーを入力、または空欄で現在のキーを保持"
        )
        google_key = st.text_input(
            "Google API Key",
            value="*" * 20 if current_keys["google"] else "",
            type="password",
            placeholder="新しいキーを入力、または空欄で現在のキーを保持"
        )
        anthropic_key = st.text_input(
            "Anthropic API Key",
            value="*" * 20 if current_keys["anthropic"] else "",
            type="password",
            placeholder="新しいキーを入力、または空欄で現在のキーを保持"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("キャンセル", use_container_width=True):
                st.session_state.show_api_settings = False
                st.rerun()
        with col2:
            if st.form_submit_button("保存", use_container_width=True, type="primary"):
                # *で始まる場合は変更なし
                if openai_key and not openai_key.startswith("*"):
                    db.save_api_keys(openai=openai_key)
                if google_key and not google_key.startswith("*"):
                    db.save_api_keys(google=google_key)
                if anthropic_key and not anthropic_key.startswith("*"):
                    db.save_api_keys(anthropic=anthropic_key)
                
                st.success("✅ APIキーを更新しました!")
                st.session_state.show_api_settings = False
                time.sleep(1)
                st.rerun()

# 新規会議作成フォーム
elif st.session_state.get("show_new_room_dialog", False):
    st.title("➕ 新規会議を作成")
    
    with st.form("new_room_form"):
        st.markdown("### 会議の設定")
        
        room_title = st.text_input("会議名", placeholder="例: 新規事業アイデア検討")
        room_description = st.text_area("説明（任意）", placeholder="会議の目的や背景")
        
        st.markdown("### 参加エージェントを選択")
        agents = db.get_all_agents()
        selected_agents = []
        
        for agent in agents:
            if st.checkbox(
                f"{agent['icon']} {agent['name']}",
                value=agent['system_default'] == 1,
                key=f"select_agent_{agent['id']}"
            ):
                selected_agents.append(agent['id'])
        
        col1, col2 = st.columns(2)
        with col1:
            cancel = st.form_submit_button("キャンセル", use_container_width=True)
        
        with col2:
            submit = st.form_submit_button("作成", use_container_width=True, type="primary")
        
        if cancel:
            st.session_state.show_new_room_dialog = False
            st.rerun()
        
        if submit:
            if room_title and selected_agents:
                room_id = db.create_room(room_title, room_description, selected_agents)
                st.session_state.current_room_id = room_id
                st.session_state.show_new_room_dialog = False
                st.success(f"✅ 会議「{room_title}」を作成しました!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("会議名とエージェントを選択してください")

# ========== メインエリア ==========
elif st.session_state.current_room_id:
    room = db.get_room(st.session_state.current_room_id)
    room_agents = db.get_room_agents(st.session_state.current_room_id)
    messages = db.get_room_messages(st.session_state.current_room_id)
    
    # タイトルバー
    st.title(f"💬 {room['title']}")
    
    # 参加メンバー表示
    member_icons = " ".join([agent['icon'] for agent in room_agents])
    st.markdown(f"**参加メンバー:** {member_icons}")
    st.markdown("---")
    
    # 2カラムレイアウト
    col_chat, col_board = st.columns([1.5, 1])
    
    with col_chat:
        # メッセージ表示エリア（高さを拡大）
        message_container = st.container(height=700)
        
        with message_container:
            for msg in messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="message-bubble" style="border-left-color: #8b5cf6;">
                        <div class="agent-name">
                            👤 あなた
                        </div>
                        <div class="message-content">{msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="message-bubble" style="border-left-color: {msg['color']};">
                        <div class="agent-name">
                            {msg['icon']} {msg['agent_name']}
                        </div>
                        <div class="message-content">{msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")  # 区切り線
        
        # 入力エリア（下に配置）
        user_input = st.text_area(
            "メッセージを入力",
            placeholder="議題や質問を入力してください...",
            height=80,
            key="user_input"
        )
        
        if st.button("🚀 送信", type="primary"):
            if user_input:
                # メッセージを保存
                db.add_message(st.session_state.current_room_id, "user", user_input)
                
                # 討論を再開（ターンカウントはリセットしない、続きから）
                st.session_state.discussion_running = True
                # フェーズは現在のまま継続
                st.rerun()
    
    
    with col_board:
        st.markdown("### 📋 議事録")
        
        board_content = json.loads(room['board_content'])
        
        # スクロール可能なコンテナ
        with st.container(height=500):
            if board_content.get('topic'):
                st.markdown(f"**テーマ:** {board_content['topic']}")
                st.markdown("---")
            
            if board_content.get('agreements'):
                st.markdown("#### ✅ 合意事項")
                for i, item in enumerate(board_content['agreements'], 1):
                    st.markdown(f"{i}. {item}")
                st.markdown("")
            
            if board_content.get('concerns'):
                st.markdown("#### ⚠️ 懸念点")
                for i, item in enumerate(board_content['concerns'], 1):
                    st.markdown(f"{i}. {item}")
                st.markdown("")
            
            if board_content.get('next_actions'):
                st.markdown("#### 📝 ネクストアクション")
                for item in board_content['next_actions']:
                    st.checkbox(item, key=f"action_{hash(item)}")
            
            if not any([board_content.get('agreements'), board_content.get('concerns'), board_content.get('next_actions')]):
                st.info("議論終了後、書記AIが議事録を作成します")


else:
    # ルームが選択されていない場合
    st.title("👋 AI Teamsへようこそ")
    st.markdown("""
    ### 使い方
    1. 左サイドバーの「➕ 新規会議」をクリック
    2. 会議名と参加エージェントを選択
    3. 議題を入力して討論を開始
    
    AIエージェントたちがプロフェッショナルな討論を展開し、
    リアルタイムで議事録を作成します。
    """)
