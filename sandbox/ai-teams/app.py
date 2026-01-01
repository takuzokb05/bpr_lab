import streamlit as st
import time
import json
import re
import traceback
from datetime import datetime, timedelta
from database import Database
from llm_client import LLMClient

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
    /* 1. 全体のフォントをモダンに (Mac/Win対応) */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
    }

    /* 2. ヘッダーの余白を削って画面を広く使う */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* 3. サイドバーの背景を少し引き締める（白ベースなら薄いグレー） */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }

    /* 4. エージェントのチャットアイコンを少し大きく */
    .stChatMessage .stChatMessageAvatar {
        width: 48px;
        height: 48px;
    }

    /* 5. "神の介入ボタン" をフローティングっぽくオシャレに */
    div.stButton > button:first-child {
        border-radius: 20px;
        font-weight: bold;
        border: none;
        transition: transform 0.1s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* 特定のボタンの色変え（キーに基づいてCSSセレクタで狙うのは難しいので汎用スタイルで） */
    /* Primaryボタン（招集など）を目立たせる */
    button[kind="primary"] {
        background-color: #000000 !important; /* Notionライクな黒 */
        color: white !important;
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
    # 1. Streamlit Secrets (Cloud Deploy)
    try:
        if "api_keys" in st.secrets:
            return {
                "google": st.secrets["api_keys"].get("google", ""),
                "openai": st.secrets["api_keys"].get("openai", ""),
                "anthropic": st.secrets["api_keys"].get("anthropic", "")
            }
    except:
        pass

    # 2. Local File
    try:
        with open("API_KEY.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        return {
            "google": lines[1].strip() if len(lines) > 1 else "",
            "openai": lines[4].strip() if len(lines) > 4 else "",
            "anthropic": lines[7].strip() if len(lines) > 7 else ""
        }
    except:
        # 3. Database Fallback
        return db.get_api_keys()

api_keys = load_api_keys()
llm_client = LLMClient(api_keys)

if "current_room_id" not in st.session_state:
    st.session_state.current_room_id = None

# ==========================================
# 定数 & ヘルパー
# ==========================================
MODEL_OPTIONS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4.1-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "google": ["gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-exp"],
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-5-sonnet-20240620"]
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
# === ヘルパー関数 ===

# === ヘルパー関数 ===

def auto_update_board(room_id, messages):
    """
    議事録（共通メモリ）を自動更新する
    議論の最新状態を反映させ、AIの認識ズレを防ぐ
    """
    try:
        # 直近の議論（最大10件）から要約を生成
        recent_log = "\n".join([f"{m['agent_name']}: {m['content']}" for m in messages[-10:] if m['role'] != 'system'])
        
        prompt = f"""
以下の議論ログから、最新の「決定事項」と「ネクストアクション」を箇条書きでまとめてください。
Markdown形式で出力せよ。

【議論ログ】
{recent_log}
"""
        # 軽量モデル（デフォルト）で要約
        summary = llm_client.generate("openai", "gpt-4o-mini", [{"role":"user", "content": prompt}])
        
        # DB更新
        db.update_room_board(room_id, summary)
        st.toast("✍️ 議事録を自動更新しました", icon="📝")
        return summary
    except Exception as e:
        print(f"Update Board Error: {e}")
        return None

def generate_agent_response(agent, room_id, messages, room_agents):
    """
    統制ロジックの核（完全版）
    1. 議事録・フェーズ・ゴールを結合した「絶対前提」を作成
    2. V字進行に基づき、役割（司令塔 vs 専門家）に応じた指示を注入
    3. LLMを実行
    """
    # 1. コンテキスト取得（共通メモリ）
    room = db.get_room(room_id)
    board_md = room.get('board_content', 'まだ合意事項はありません。')
    first_msg = next((m for m in messages if m['role'] == 'user'), None)
    goal_text = f"【ゴール】 {first_msg['content']}" if first_msg else "議題未設定"
    
    # 2. フェーズ判定（アジェンダ管理）
    turn_count = len([m for m in messages if m['role'] == 'assistant'])
    if turn_count < 5: 
        phase_msg = "【フェーズ: 1. 発散】批判せず、可能性を広げてください。"
    elif turn_count < 12: 
        phase_msg = "【フェーズ: 2. 選別】実現性とコストから、議事録の案を厳しく批評してください。"
    else: 
        phase_msg = "【フェーズ: 3. 収束】これまでの結論を具体的なアクションプラン（ToDo）にまとめてください。"

    # 3. 役割別指示（V字進行用）
    is_moderator = agent.get('category') == 'facilitation'
    
    if is_moderator:
        role_instr = """
あなたは進行役（司令塔）です。
1. フェーズに従い、議論をリードしてください。
2. メンバーの発言を要約し、論点を整理してください。
3. 次に発言させるべきメンバーを指名し、文末に必ず `[[NEXT: agent_id]]` を出力してください。
4. 【重要】議論が十分にまとまった、あるいはユーザーから「終了」「まとめ」等の指示があった場合は、まとめの言葉の後に `[[FINISH]]` とだけ出力して議論を終了させてください。
"""
    else:
        role_instr = """
あなたは専門家メンバーです。
1. 議事録（合意事項）を前提とし、蒸し返さないでください。
2. 司会や他メンバーの問いに、専門的見地から短く鋭く答えてください（Yes,and / No,because）。
3. 発言後、議論のバトンを必ず司会（モデレーター）に戻してください（NEXTタグは不要）。
"""

    # 4. 統合システムプロンプト構築
    member_list = "\n".join([f"- {a['name']} (ID:{a['id']}): {a['role'][:30]}..." for a in room_agents])
    
    # AIの脳に直接注入する「絶対ルール」
    extra_system_prompt = f"""
{goal_text}

{phase_msg}

【現在の合意事項（最新の議事録）】
{board_md}

【参加メンバー一覧（ID付き）】
{member_list}

{role_instr}

【ルール】
- 議事録の内容を蒸し返さず、一歩進んだ議論をしてください。
"""

    # 5. メッセージ構築 (Systemは llm_client 側で結合されるが、念のためここでも最小限定義)
    base_system = f"あなたは【{agent['name']}】です。\n役割: {agent['role']}\n200文字以内で簡潔に発言してください。"

    # 直近ログ（最新5件）
    recent_msgs = [m for m in messages if m['role'] != 'system'][-5:]
    clean_history = []
    for m in recent_msgs:
         cln = re.sub(r"\[\[NEXT:.*?\]\]", "", m['content']).strip()
         clean_history.append({"role": m['role'], "content": cln})

    input_msgs = [{"role": "system", "content": base_system}] + clean_history
    
    # llm_client に extra_system_prompt を渡し、脳の最上層に注入させる
    return llm_client.generate(agent['provider'], agent['model'], input_msgs, extra_system_prompt=extra_system_prompt)

@st.dialog("エージェント管理")
def manage_agents():
    tab_new, tab_edit = st.tabs(["➕ 新規作成", "📝 編集・削除"])
    
    # カテゴリ定義
    CATEGORIES = {
        "facilitation": "🎯 ファシリテーション",
        "logic": "🧠 論理・分析",
        "creative": "🎨 クリエイティブ",
        "empathy": "💝 共感・サポート",
        "specialist": "🔧 スペシャリスト"
    }
    
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
        
        c3, c4 = st.columns(2)
        with c3:
            color = st.color_picker("イメージカラー", "#3b82f6", key="new_color")
        with c4:
            category = st.selectbox("カテゴリ", list(CATEGORIES.keys()), 
                                   format_func=lambda x: CATEGORIES[x], key="new_category")
        
        if st.button("作成", key="create_btn", type="primary"):
            if name and role:
                db.create_agent(name, icon, color, role, model, provider, category)
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
            
            ec1, ec2 = st.columns(2)
            with ec1:
                e_provider = st.selectbox("プロバイダー", ["openai", "google", "anthropic"], 
                                        index=["openai","google","anthropic"].index(target['provider']) if target['provider'] in ["openai","google","anthropic"] else 0,
                                        key=f"e_prov_{target_id}")
            with ec2:
                e_model = st.selectbox("モデル", MODEL_OPTIONS.get(e_provider, [target['model']]), key=f"e_mod_{target_id}")
            
            e_category = st.selectbox("カテゴリ", list(CATEGORIES.keys()),
                                     index=list(CATEGORIES.keys()).index(target.get('category', 'specialist')) if target.get('category') in CATEGORIES else 4,
                                     format_func=lambda x: CATEGORIES[x], key=f"e_cat_{target_id}")
            
            c1, c2 = st.columns([1,1])
            if c1.button("💾 保存", key=f"save_{target_id}"):
                db.update_agent(target_id, e_name, target['icon'], target['color'], e_role, e_model, e_provider, e_category)
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
    @st.dialog("＋ 新しい会議室を作成", width="large")
    def create_new_room_dialog():
        default_title = f"会議 {datetime.now().strftime('%m/%d %H:%M')}"
        title = st.text_input("会議名", value=default_title)
        
        all_agents = db.get_all_agents()
        
        # カテゴリ定義
        CATEGORIES = {
            "recommended": "⭐ おすすめ",
            "facilitation": "🎯 ファシリテーション",
            "logic": "🧠 論理・分析",
            "creative": "🎨 クリエイティブ",
            "empathy": "💝 共感・サポート",
            "specialist": "🔧 スペシャリスト"
        }
        
        # カテゴリ別にエージェントを整理
        categorized_agents = {cat: [] for cat in CATEGORIES.keys()}
        
        # デフォルトエージェント（おすすめ）
        default_ids = [a['id'] for a in all_agents if a.get('system_default')]
        categorized_agents["recommended"] = [a for a in all_agents if a.get('system_default')]
        
        # カテゴリ別に分類
        for agent in all_agents:
            cat = agent.get('category', 'specialist')
            if cat in categorized_agents:
                categorized_agents[cat].append(agent)
        
        # 選択状態を保持
        if 'selected_agent_ids' not in st.session_state:
            st.session_state.selected_agent_ids = set(default_ids)
        
        st.markdown("### 👥 チームメンバーを選択")
        st.caption("カテゴリごとにタブで整理されています。複数選択可能です。")
        
        # タブでカテゴリ分け (Hick's Law対策)
        tabs = st.tabs([CATEGORIES[cat] for cat in CATEGORIES.keys()])
        
        for i, (cat_key, cat_name) in enumerate(CATEGORIES.items()):
            with tabs[i]:
                agents_in_cat = categorized_agents[cat_key]
                
                if not agents_in_cat:
                    st.info(f"このカテゴリにはエージェントがいません")
                    continue
                
                # グリッド表示 (1行に3枚のカード)
                cols = st.columns(3)
                for j, agent in enumerate(agents_in_cat):
                    with cols[j % 3]:
                        # カード形式で表示
                        is_selected = agent['id'] in st.session_state.selected_agent_ids
                        
                        # チェックボックスの状態変更を検知
                        selected = st.checkbox(
                            f"{agent['icon']} **{agent['name']}**",
                            value=is_selected,
                            key=f"agent_select_{cat_key}_{agent['id']}"
                        )
                        
                        # 役割の簡易説明
                        role_preview = agent['role'][:60] + "..." if len(agent['role']) > 60 else agent['role']
                        st.caption(role_preview)
                        
                        # 選択状態を更新
                        if selected and agent['id'] not in st.session_state.selected_agent_ids:
                            st.session_state.selected_agent_ids.add(agent['id'])
                        elif not selected and agent['id'] in st.session_state.selected_agent_ids:
                            st.session_state.selected_agent_ids.discard(agent['id'])
        
        # 選択中のメンバー表示
        st.divider()
        selected_count = len(st.session_state.selected_agent_ids)
        st.markdown(f"### 選択中: {selected_count}名")
        
        if selected_count > 0:
            selected_agents = [a for a in all_agents if a['id'] in st.session_state.selected_agent_ids]
            cols_display = st.columns(min(selected_count, 6))
            for idx, agent in enumerate(selected_agents[:6]):
                with cols_display[idx]:
                    st.markdown(f"{agent['icon']}")
                    st.caption(agent['name'])
            if selected_count > 6:
                st.caption(f"他 {selected_count - 6}名")
        
        first_prompt = st.text_area("最初の指示 (任意)", placeholder="例: 今期のマーケティング施策についてブレストしたい")
        
        if st.button("🚀 会議を開始", type="primary", use_container_width=True):
            if len(st.session_state.selected_agent_ids) == 0:
                st.error("少なくとも1名のエージェントを選択してください")
            else:
                new_id = db.create_room(title, first_prompt, list(st.session_state.selected_agent_ids))
                
                if first_prompt:
                    db.add_message(new_id, "user", first_prompt)
                
                # 選択状態をリセット
                st.session_state.selected_agent_ids = set(default_ids)
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

    # ルーム内設定 (リネーム & メンバー管理)
    if st.session_state.current_room_id:
        room_id = st.session_state.current_room_id
        st.markdown("---")
        
        # 頻繁に使うのでデフォルト展開でも良いが、画面スペース節約のため畳んでおく
        with st.expander("⚙️ 会議室の設定 & メンバー"):
            current_room = next((r for r in all_rooms if r['id'] == room_id), None)
            
            if current_room:
                # 1. リネーム
                new_title = st.text_input("会議室名", value=current_room['title'])
                if new_title != current_room['title']:
                    if st.button("名称を更新"):
                        db.update_room_title(current_room['id'], new_title)
                        st.session_state.current_room_id = current_room['id']
                        st.rerun()
                
                st.divider()
                
                # 2. メンバー管理 (Reactive - コールバック方式)
                st.caption("👥 参加メンバー (リアルタイム変更)")
                all_agents = db.get_all_agents()
                # 初期表示用（まだセッションステートがない場合）
                current_agent_ids = db.get_room_agent_ids(room_id)
                
                agent_map = {a['id']: f"{a['icon']} {a['name']}" for a in all_agents}
                
                def on_member_change():
                    # session_stateから最新の値を取得
                    key = f"members_{room_id}"
                    if key in st.session_state:
                        selected = st.session_state[key]
                        log = db.update_room_agents_diff(room_id, selected)
                        if log:
                            db.add_message(room_id, "system", log)
                            st.toast("✅ メンバー変更")
                
                # Multiselect with Callback
                # 注意: defaultを指定しつつkeyを指定すると、初回ロード時に警告が出ることがあるが、
                # keyが未定義の時だけdefaultを使うStreamlitの挙動を利用する。
                st.multiselect(
                    "メンバー編集",
                    options=list(agent_map.keys()),
                    format_func=lambda x: agent_map[x],
                    default=current_agent_ids,
                    key=f"members_{room_id}",
                    on_change=on_member_change,
                    label_visibility="collapsed"
                )
                
                # 表示用IDリスト
                disp_ids = st.session_state.get(f"members_{room_id}", current_agent_ids)
                
                # 参加者のアバター表示
                if disp_ids:
                    st.write("")
                    cols_av = st.columns(6)
                    active_agents = [a for a in all_agents if a['id'] in disp_ids]
                    for i, ag in enumerate(active_agents):
                        with cols_av[i % 6]:
                            st.caption(f"{ag['icon']}")

            st.caption("※ルーム削除は「🗂 履歴一覧・管理」から")


def render_dashboard():
    if st.session_state.current_room_id is None:
        st.title("🚀 AI Teams Command Center")
        st.write("各分野のエキスパートAIが、あなたの課題解決を支援します。")
        
        st.markdown("---")

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

        # グリッドレイアウト
        c1, c2, c3 = st.columns(3)
        
        # スタイル付きのカード表示関数
        def draw_card(col, tpl):
            with col:
                with st.container(border=True):
                    # ヘッダーエリア
                    hd_c1, hd_c2 = st.columns([5, 1])
                    hd_c1.markdown(f"### {tpl['icon']} {tpl['name']}")
                    if hd_c2.button("⚙️", key=f"conf_{tpl['id']}", help="構成を編集"):
                         configure_template(tpl)

                    # 説明文（プロンプトの冒頭）
                    desc = tpl.get('prompt','')[:40] + "..." if tpl.get('prompt') else "（設定なし）"
                    st.caption(desc)
                    
                    st.write("") # Spacer
                    
                    if st.button("チームを招集", key=f"launch_{tpl['id']}", use_container_width=True, type="primary"):
                        # Room作成
                        new_id = db.create_room(tpl['name'], tpl.get('prompt',''), tpl['default_agent_ids'])
                        if tpl.get('prompt'):
                            db.add_message(new_id, "user", tpl['prompt'])
                        st.session_state.current_room_id = new_id
                        st.rerun()

        # テンプレート展開
        try:
            templates = db.get_templates()
        except:
            templates = []

        if not templates:
             st.info("DB初期化中... リロードしてください")
        
        for i, tpl in enumerate(templates):
            # 3列に割り振るロジック
            col = [c1, c2, c3][i % 3]
            draw_card(col, tpl)

        st.markdown("#### 📂 最近のプロジェクト")
        recents = db.get_all_rooms()
        recents.sort(key=lambda x: x['updated_at'] or x['created_at'], reverse=True)
        
        # 最近のプロジェクトもカードグリッドで
        rc1, rc2, rc3 = st.columns(3)
        for i, r in enumerate(recents[:3]):
            with [rc1, rc2, rc3][i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{r['title']}**")
                    st.caption(f"📅 {r['created_at'][:10]}")
                    st.caption(f"{r['description'][:30]}..." if r.get('description') else "---")
                    if st.button("再開", key=f"resume_db_{r['id']}", use_container_width=True):
                        st.session_state.current_room_id = r['id']
                        st.rerun()

# ==========================================
# メイン: ルーム機能 (Unified Fragment)
# ==========================================
@st.fragment
def render_active_chat(room_id, auto_mode):
    """
    チャットエリア（Fragment化）
    画面全体のリロード（ホワイトアウト）を防ぎ、ここだけを更新する。
    """
    room = db.get_room(room_id)
    st.subheader(f"💬 {room['title']}")
    
    # チャットコンテナ（スクロール可能）
    container = st.container(height=650)
    messages = db.get_room_messages(room_id)
    
    with container:
        if not messages:
            st.info("👋 ようこそ、オーナー。チームは待機しています。最初の議題を投げかけてください。")
        
        for msg in messages:
            with st.chat_message(msg['role'], avatar=msg.get('icon')):
                r_name = msg.get('agent_role', 'Participant')
                if not r_name: r_name = "User" if msg['role'] == "user" else "AI"
                
                # ヘッダー
                st.markdown(f"<div class='agent-header'><span class='agent-name'>{msg.get('agent_name', 'User')}</span><span class='agent-role'>({r_name[:15]}...)</span></div>", unsafe_allow_html=True)
                
                # 添付ファイルの表示
                if msg.get('attachments'):
                    import base64
                    try:
                        attachments = json.loads(msg['attachments'])
                        for att in attachments:
                            file_name = att.get('name', 'file')
                            file_type = att.get('type', '')
                            file_data = att.get('data', '')
                            
                            # 画像の場合は表示
                            if file_type.startswith('image/'):
                                st.image(base64.b64decode(file_data), caption=file_name, use_container_width=True)
                            # PDFの場合はダウンロードリンク
                            elif file_type == 'application/pdf':
                                st.markdown(f"📄 **{file_name}** ({att.get('size', 0) // 1024} KB)")
                                st.download_button(
                                    label="PDFをダウンロード",
                                    data=base64.b64decode(file_data),
                                    file_name=file_name,
                                    mime=file_type,
                                    key=f"download_{msg['id']}_{file_name}"
                                )
                            # テキストファイルの場合は内容プレビュー
                            elif file_type.startswith('text/'):
                                text_content = base64.b64decode(file_data).decode('utf-8')
                                with st.expander(f"📝 {file_name}"):
                                    st.code(text_content[:500] + ("..." if len(text_content) > 500 else ""))
                    except Exception as e:
                        st.caption(f"⚠️ 添付ファイルの表示エラー: {e}")
                
                # 本文 (タグを非表示にする)
                clean_content = re.sub(r"\[\[NEXT:.*?\]\]", "", msg['content']).strip()
                st.write(clean_content)
                
                # 👑 ディレクターズ・カット
                with st.popover("✏️", help="脚本修正 & 死に戻り"):
                    new_val = st.text_area("修正", value=msg['content'], key=f"edit_area_{msg['id']}", height=120)
                    st.caption("※以降の未来を消去して再開します")
                    if st.button("書き換え ↺", key=f"save_edit_{msg['id']}", type="primary"):
                        db.edit_message_and_truncate(room_id, msg['id'], new_val)
                        st.rerun()

                # 引用アクション (AIのみ)
                if msg['role'] != 'user':
                    c1, c2, _ = st.columns([1,1,10])
                    if c1.button("🔍", key=f"deep_{msg['id']}"):
                         db.add_message(room_id, "user", f"@{msg.get('agent_name')}さん、今の「{clean_content[:20]}...」について具体的に説明してください。")
                         st.rerun()
                    if c2.button("🔥", key=f"crit_{msg['id']}"):
                         db.add_message(room_id, "user", f"@{msg.get('agent_name')}さんの意見に反論してください。")
                         st.rerun()

    # 介入ボタン
    c_int = st.columns([1, 1, 1, 4])
    if c_int[0].button("⏹️ 停止", help="議論を打ち切りまとめさせる"):
        db.add_message(room_id, "user", "議論を終了します。これまでの結論をまとめてください。")
        st.rerun()
    if c_int[1].button("🤔 整理", help="論点整理"):
        db.add_message(room_id, "user", "現状の論点を整理してください。")
        st.rerun()

    # ファイルアップロード機能
    st.markdown("---")
    st.caption("📎 ファイル添付（画像・PDF・テキスト対応）")
    
    uploaded_files = st.file_uploader(
        "ファイルを選択",
        type=["png", "jpg", "jpeg", "webp", "gif", "pdf", "txt", "md", "csv", "json"],
        accept_multiple_files=True,
        key=f"file_upload_{room_id}",
        label_visibility="collapsed"
    )
    
    # 入力欄
    prompt = st.chat_input("指示を入力...", key=f"chat_{room_id}")
    
    if prompt or uploaded_files:
        import base64
        
        attachments_data = []
        
        # ファイルを処理
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_bytes = uploaded_file.read()
                file_b64 = base64.b64encode(file_bytes).decode('utf-8')
                
                attachments_data.append({
                    "name": uploaded_file.name,
                    "type": uploaded_file.type,
                    "size": len(file_bytes),
                    "data": file_b64
                })
        
        # メッセージを保存
        message_text = prompt if prompt else f"[{len(attachments_data)}個のファイルを添付]"
        attachments_json = json.dumps(attachments_data) if attachments_data else None
        
        db.add_message(room_id, "user", message_text, attachments=attachments_json)
        st.rerun()

    # === 自動進行ロジック (Fragment内ループ & 統制システム) ===
    last_msg = messages[-1] if messages else None
    last_role = last_msg['role'] if last_msg else 'system'
    
    # 実行条件: 
    # 1. ユーザー発言後 -> 自動実行
    # 2. auto_mode ON かつ AIの発言後 -> 継続
    should_run = False
    
    if last_role == 'user':
        should_run = True
    elif auto_mode and last_role == 'assistant' and len(messages) < 60: # 最大ターン拡張
        # 終了判定: タグまたはキーワード
        if "[[FINISH]]" in last_msg['content'] or "議論を終了" in last_msg['content']:
            should_run = False
        else:
            should_run = True
        
    if should_run:
        time.sleep(1.5) # 間を取る
        
        with container:
            room_agents = db.get_room_agents(room_id)
            if not room_agents: return

            # 書記などの裏方を除外 (Active Agentsのみ)
            # これにより「書記」が勝手に指名されたり発言したりするのを防ぐ
            active_agents = [a for a in room_agents if "書記" not in a['name']]
            if not active_agents: active_agents = room_agents # フォールバック

            # モデレーター特定
            moderator = next((a for a in active_agents if a.get('category') == 'facilitation'), None)
            if not moderator:
                moderator = next((a for a in active_agents if "モデレーター" in a['name'] or "司会" in a['name']), active_agents[0])

            # --- V字進行型 v2 (State-Based) ---
            # Streamlitのrerun対策として、次の話者をsession_stateで管理する
            state_key = f"next_speaker_{room_id}"
            next_agent = None
            last_agent_id = last_msg.get('agent_id')

            # 1. ユーザー発言直後 -> 強制的にモデレーター
            if last_role == 'user':
                st.session_state[state_key] = moderator['id']
            
            # 2. AI発言後のバトンパス判定
            elif last_role == 'assistant':
                # A. モデレーターが喋った -> 次は指名されたメンバー
                if last_agent_id == moderator['id']:
                    match = re.search(r"\[\[NEXT:\s*(\d+)\]\]", last_msg['content'])
                    if match:
                        try:
                            t_id = int(match.group(1))
                            # IDの有効性チェック
                            if any(a['id'] == t_id for a in active_agents):
                                st.session_state[state_key] = t_id
                        except:
                            pass
                # B. メンバーが喋った -> 次は必ずモデレーター
                else:
                    st.session_state[state_key] = moderator['id']

            # 3. ステートから次のエージェントを決定
            target_id = st.session_state.get(state_key)
            if target_id:
                next_agent = next((a for a in active_agents if a['id'] == target_id), None)

            # 4. フォールバック（ステート喪失時や指名ミス時）
            if not next_agent:
                # メンバーリストからモデレーター以外をランダム選出（無限ループ防止）
                others = [a for a in active_agents if a['id'] != moderator['id']]
                if others and last_agent_id == moderator['id']:
                     next_idx = len(messages) % len(others)
                     next_agent = others[next_idx]
                else:
                     next_agent = moderator

            # 2. 生成プロセス
            with st.chat_message("assistant", avatar=next_agent['icon']):
                ph = st.empty()
                ph.markdown(f":grey[{next_agent['name']} が思考中...]")
                
                try:
                    # 統合された統制ロジック関数を呼び出し
                    response = generate_agent_response(next_agent, room_id, messages, room_agents)
                    
                    # UX: 完了トースト
                    st.toast(f"{next_agent['name']} が発言しました", icon="✅")
                    
                    # 表示用テキスト (タグを除去)
                    display_text = re.sub(r"\[\[NEXT:.*?\]\]", "", response)
                    display_text = re.sub(r"\[\[FINISH\]\]", "", display_text).strip()
                    
                    # 表示更新
                    role_html = f"<span class='agent-role'>({next_agent.get('role', '')[:10]}...)</span>"
                    html = f"<div class='agent-header'><span class='agent-name'>{next_agent['name']}</span>{role_html}</div>\n\n{display_text}"
                    ph.markdown(html, unsafe_allow_html=True)
                    
                    # DB保存 (タグ付きのまま保存し、ロジックで利用する)
                    db.add_message(room_id, "assistant", response, next_agent['id'])
                    
                    # 終了処理 (Exit Protocol)
                    if "[[FINISH]]" in response:
                        temp_msgs = messages + [{'role':'assistant', 'content':response, 'agent_name':next_agent['name']}]
                        auto_update_board(room_id, temp_msgs)
                        st.balloons()
                        st.toast("🏁 議論が終了しました", icon="🛑")
                        st.rerun()
                    
                    # 議事録自動更新 (3ターンに1回)
                    # 最新の文脈を反映させる
                    turn_count = len([m for m in messages if m['role'] == 'assistant']) + 1
                    if turn_count % 3 == 0:
                        temp_msgs = messages + [{'role':'assistant', 'content':response, 'agent_name':next_agent['name']}]
                        auto_update_board(room_id, temp_msgs)
                    
                    # Fragmentリラン (次のターンへ)
                    st.rerun()
                    
                except Exception as e:
                    ph.error(f"Error: {e}")
                    traceback.print_exc()
@st.fragment
def render_room_interface(room_id, auto_mode):
    col_chat, col_info = st.columns([2, 1.3]) # リキッドレイアウト調整
    
    # 左: チャット (Fragmentとして独立)
    with col_chat:
        render_active_chat(room_id, auto_mode)

    # 右: 情報パネル
    with col_info:
        # DBからルーム情報を取得
        room = db.get_room(room_id)
        
        with st.container(border=True):
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



# ==========================================
# APP ROUTING
# ==========================================
if st.session_state.current_room_id:
    render_room_interface(st.session_state.current_room_id, auto_mode)
else:
    render_dashboard()
