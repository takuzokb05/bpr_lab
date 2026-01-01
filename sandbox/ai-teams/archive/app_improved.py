import streamlit as st
import time
import json
import re
from database import Database
from llm_client import LLMClient

# ==========================================
# 設定
# ==========================================
st.set_page_config(
    page_title="AI Teams",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS (見やすさ向上)
st.markdown("""
<style>
    .stTextArea textarea {
        font-size: 16px;
    }
    .agent-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# データベース接続
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# APIキー読み込み
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

# セッション状態初期化
if "current_room_id" not in st.session_state:
    st.session_state.current_room_id = None
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "discussion_running" not in st.session_state:
    st.session_state.discussion_running = False

# ==========================================
# サイドバー (会議選択・作成)
# ==========================================
with st.sidebar:
    st.title("📂 会議室管理")
    
    # ルーム選択
    rooms = db.get_all_rooms()
    room_options = {r['id']: r['title'] for r in rooms}
    
    selected_room_id = st.selectbox(
        "会議室を選択",
        options=list(room_options.keys()),
        format_func=lambda x: room_options[x],
        index=0 if rooms else None
    )
    
    if selected_room_id != st.session_state.current_room_id:
        st.session_state.current_room_id = selected_room_id
        # メッセージ数をカウントしてターン数を設定
        messages = db.get_room_messages(selected_room_id)
        st.session_state.turn_count = len(messages)
        st.session_state.discussion_running = False
        st.rerun()

    with st.expander("➕ 新規会議作成"):
        with st.form("create_room"):
            new_title = st.text_input("会議名")
            new_desc = st.text_area("説明")
            
            agents = db.get_all_agents()
            default_agents = [a['id'] for a in agents if a['system_default']]
            selected_agents = st.multiselect(
                "参加エージェント",
                options=[a['id'] for a in agents],
                format_func=lambda x: next((a['name'] for a in agents if a['id'] == x), "Unknown"),
                default=default_agents
            )
            
            if st.form_submit_button("作成"):
                new_id = db.create_room(new_title, new_desc, selected_agents)
                st.session_state.current_room_id = new_id
                st.session_state.turn_count = 0
                st.session_state.discussion_running = False
                st.rerun()

# ==========================================
# メイン画面
# ==========================================

if not st.session_state.current_room_id:
    st.info("👈 左のメニューから会議室を選択または作成してください")
    st.stop()

col_chat, col_board = st.columns([2, 1])

# 議事録表示関数
def display_board(container, room_id):
    room = db.get_room(room_id)
    try:
        content = json.loads(room['board_content'])
    except:
        content = {}
    
    with container:
        st.subheader(f"📋 議事録: {room['title']}")
        st.markdown("---")
        if content.get('topic'): st.markdown(f"**テーマ**: {content['topic']}")
        
        if content.get('agreements'):
            st.markdown("### ✅ 合意事項")
            for item in content['agreements']: st.markdown(f"- {item}")
            
        if content.get('concerns'):
            st.markdown("### ⚠️ 懸念点")
            for item in content['concerns']: st.markdown(f"- {item}")
            
        if content.get('next_actions'):
            st.markdown("### 📝 ネクストアクション")
            for item in content['next_actions']: st.markdown(f"- [ ] {item}")

# 右カラム: 議事録 (Placeholder)
board_placeholder = col_board.empty()
display_board(board_placeholder, st.session_state.current_room_id)

# 左カラム: チャット
with col_chat:
    chat_container = st.container(height=700)
    
    # 過去ログ表示
    messages = db.get_room_messages(st.session_state.current_room_id)
    with chat_container:
        for msg in messages:
            with st.chat_message(msg['role'], avatar=msg.get('icon')):
                if msg['role'] != 'user':
                    st.write(f"**{msg.get('agent_name')}**")
                st.write(msg['content'])

    # 入力フォーム
    if prompt := st.chat_input("メッセージを入力して議論を開始/再開..."):
        # ユーザーメッセージ即時表示
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt)
        
        # DB保存
        db.add_message(st.session_state.current_room_id, "user", prompt)
        
        # 自動議論フラグON
        st.session_state.discussion_running = True


# ==========================================
# 自動議論ロジック (リロードなしで実行)
# ==========================================

if st.session_state.discussion_running:
    room_agents = db.get_room_agents(st.session_state.current_room_id)
    
    # ループ実行 (最大16ターンまで)
    # st.rerunせずに、ここで連続処理して追記していく
    
    while st.session_state.turn_count <= 16:
        turn = st.session_state.turn_count
        
        # フェーズ管理
        phase = "free"
        next_agent = None
        
        if turn == 0:
            phase = "opening"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn == 1:
            phase = "divergence"
            idea_agent = next((a for a in room_agents if "アイデア" in a['name']), None)
            next_agent = idea_agent if idea_agent else room_agents[1 % len(room_agents)]
        elif turn <= 6:
            next_agent = room_agents[turn % len(room_agents)]
        elif turn == 7:
            phase = "convergence"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn <= 12:
            next_agent = room_agents[turn % len(room_agents)]
        elif turn == 13:
            phase = "conclusion"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn < 16:
            next_agent = room_agents[0]
        else:
            # 終了
            break

        if not next_agent:
            break

        # UI更新: 思考中...
        with chat_container:
            with st.chat_message("assistant", avatar=next_agent['icon']):
                st.write(f"**{next_agent['name']}** (思考中...)")
                
                # Context構築
                msgs = db.get_room_messages(st.session_state.current_room_id)
                recent_msgs = msgs[-8:]
                context = [{"role": ("user" if m['role']=="user" else "assistant"), "content": m['content']} for m in recent_msgs]
                
                # Prompt
                if "モデレーター" in next_agent['name']:
                    sys_prompt = f"あなたは{next_agent['name']}です。役割:{next_agent['role']}。フェーズ:{phase}。司会者として議論を整理してください。50文字以内。"
                else:
                    sys_prompt = f"あなたは{next_agent['name']}です。役割:{next_agent['role']}。詳細に具体的に意見を述べてください。"
                
                try:
                    # 生成
                    response = llm_client.generate(next_agent['provider'], next_agent['model'], [{"role":"system", "content":sys_prompt}] + context)
                    
                    # 思考中メッセージを上書きするのは難しいので、思考中表示の後に追記する形にするか、
                    # Streamlitのemptyを使って書き換える。
                    # ここではシンプルに結果を表示（思考中テキストは残るが、UX的には「考えた結果」として許容範囲）
                    # あるいは empty を使う。
                except Exception as e:
                    st.error(f"Error: {e}")
                    break

            # 思考中プレースホルダーを使いたいが、withブロック内での制御が複雑になるので
            # 実際には「思考中」を出さず、スピナーを使うの手
            # しかしホワイトアウト禁止なので、メッセージ枠だけ出して empty に書くのがベスト
        
        # 本番描画 (書き直し) - 上のwithブロックは「思考中」用だったが、実装を変える。
        # シンプルに: 
        
        with chat_container:
            with st.chat_message("assistant", avatar=next_agent['icon']):
                message_placeholder = st.empty()
                message_placeholder.markdown("🌀 *思考中...*")
                
                # 生成処理
                try:
                    msgs = db.get_room_messages(st.session_state.current_room_id)
                    recent_msgs = msgs[-8:]
                    context = [{"role": ("user" if m['role']=="user" else "assistant"), "content": m['content']} for m in recent_msgs]
                    
                    if "モデレーター" in next_agent['name']:
                        sys_prompt = f"あなたは{next_agent['name']}です。役割:{next_agent['role']}。フェーズ:{phase}。司会者として議論を整理してください。50文字以内。"
                    else:
                        sys_prompt = f"あなたは{next_agent['name']}です。役割:{next_agent['role']}。詳細に具体的に意見を述べてください。"

                    response = llm_client.generate(next_agent['provider'], next_agent['model'], [{"role":"system", "content":sys_prompt}] + context)
                    
                    # 完了したら書き換え
                    message_placeholder.markdown(f"**{next_agent['name']}**\n\n{response}")
                    
                    # DB保存
                    db.add_message(st.session_state.current_room_id, "assistant", response, next_agent['id'])
                    
                    # ターン進行
                    st.session_state.turn_count += 1
                    
                except Exception as e:
                    message_placeholder.error(f"Error: {str(e)}")
                    break
        
        # 少し待機
        time.sleep(1)
    
    # ループ終了後の処理
    st.session_state.discussion_running = False
    
    # 議事録生成 (最後だけ)
    if st.session_state.turn_count >= 16:
        with chat_container:
            st.info("📝 書記AIが議事録をまとめています...")
            
        scribe = next((a for a in room_agents if "書記" in a['name']), None)
        if scribe:
            try:
                all_msgs = db.get_room_messages(st.session_state.current_room_id)
                text = "\n".join([f"{m.get('agent_name','User')}: {m['content']}" for m in all_msgs])
                prompt = f"議論をまとめ、JSON形式(topic, agreements, concerns, next_actions)で出力してください。\n{text}"
                res = llm_client.generate(scribe['provider'], scribe['model'], [{"role":"user", "content":prompt}])
                
                match = re.search(r'\{.*\}', res, re.DOTALL)
                if match:
                    content = json.loads(match.group())
                    db.update_room_board(st.session_state.current_room_id, content)
                    # 議事録エリア更新
                    display_board(board_placeholder, st.session_state.current_room_id)
                    
            except Exception as e:
                st.error(f"Scribe Error: {e}")

    # 最終的な状態を保存するために一度だけリランしてもいいが、
    # ホワイトアウト嫌いならリランしない。
    # 次のアクション（入力）時に自動的に整合性が取れる。
