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

# --- 2026 Model Migration (Auto-Fix) ---
# ユーザーの既存データに残っている古いモデルIDを最新版に自動置換する
if "migration_done_2026" not in st.session_state:
    try:
        agents = db.get_all_agents()
        migration_map = {
            "claude-3-5-sonnet-20241022": "claude-sonnet-4-5",
            "claude-3-5-sonnet-latest": "claude-sonnet-4-5", # 3.5 latestも4.5へ強制移行
            "claude-3-5-haiku-20241022": "claude-haiku-4-5",
            "claude-3-5-sonnet-20240620": "claude-sonnet-4-5",
            "claude-3-5-haiku-latest": "claude-haiku-4-5"
        }
        count = 0
        for ag in agents:
            current_model = ag['model']
            if current_model in migration_map:
                new_model = migration_map[current_model]
                # 全フィールドを引き継いで更新
                db.update_agent(
                    ag['id'], ag['name'], ag['icon'], ag['color'], ag['role'],
                    new_model, ag['provider'], ag.get('category', 'specialist')
                )
                count += 1
        if count > 0:
            print(f"✅ Migrated {count} agents to 2026 models.")
            st.toast(f"システム更新: {count}体のエージェントを最新モデルに移行しました", icon="🆙")
    except Exception as e:
        print(f"Migration failed: {e}")
    
    st.session_state.migration_done_2026 = True

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
    "openai": ["gpt-5", "gpt-5.2", "gpt-5-mini", "o3-mini", "o1"],
    "google": ["gemini-3-pro-preview", "gemini-3-pro", "gemini-3-flash", "gemini-2.0-flash-exp"],
    "anthropic": [
        "claude-opus-4-5", 
        "claude-sonnet-4-5", 
        "claude-haiku-4-5"
    ]
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
    議事録（共通メモリ）を自動更新する。
    薄い要約ではなく、「知識建築家」として論理構造と未解決の矛盾を可視化する。
    """
    try:
        # 直近だけでなく、ある程度の文脈を含める（最大20件）
        recent_log = "\n".join([f"{m['agent_name']}: {m['content']}" for m in messages[-20:] if m['role'] != 'system'])
        
        # 議題を推定（メッセージから）
        current_topic = "議論のテーマ" 
        
        prompt = f"""
あなたはプロジェクトの「知識建築家（Knowledge Architect）」です。
これまでの議論ログから、以下の情報を構造化し、Markdown形式で出力してください。
単なる要約は禁止です。論理の整合性、対立点、未解決の課題を深く分析して記録してください。

## 出力フォーマット
**議題**: (ログから推定されるテーマ)

### 🏗️ 論理構造と合意事項
- (決定事項だけでなく、なぜその決定に至ったかの「論理的根拠」を明記)
- (合意形成されたプロセスを重要な意思決定ポイントと共に記述)

### ⚔️ 対立軸と未解決の矛盾 (Crucial Conflicts)
- (「A案 vs B案」のような対立構造があれば明記)
- (未だ解消されていない「論理の矛盾」や「懸念点」を鋭く指摘)

### 🔭 Next Actions & 探索領域
- (誰が何をすべきか具体的なアクション)
- (次に深堀りすべき「問い」は何か)

【議論ログ】
{recent_log}
"""
        # ロジック理解に強いモデル推奨だが、コストバランスで4o-miniか、より賢いモデルを使うか
        # ユーザー要望で「薄い」のが嫌なので、少し強めのモデルを使う手もあるが、一旦4o-miniでプロンプト強度で勝負
        summary = llm_client.generate("openai", "gpt-4o-mini", [{"role":"user", "content": prompt}])
        
        # DB更新
        db.update_room_board(room_id, summary)
        st.toast("✍️ 議事録（構造図）を更新しました", icon="�")
        return summary
    except Exception as e:
        print(f"Update Board Error: {e}")
        return None

def generate_agent_response(agent, room_id, messages, room_agents):
    """
    統制ロジックの核（Paradigm Shift Edition）
    1. カテゴリ分布から「モード（深化 vs 創発）」を決定
    2. V字進行に基づき、詳細なコンテキスト注入と長文思考を誘導
    3. LLMを実行（max_tokens拡張済み）
    """
    # 1. コンテキスト取得（共通メモリ）
    room = db.get_room(room_id)
    board_md = room.get('board_content', 'まだ合意事項はありません。')
    first_msg = next((m for m in messages if m['role'] == 'user'), None)
    goal_text = f"【ゴール】 {first_msg['content']}" if first_msg else "議題未設定"
    
    # 2. モード分析 & フェーズ判定
    # カテゴリ分布をチェック
    cats = [a.get('category') for a in room_agents]
    logic_count = cats.count('logic') + cats.count('specialist')
    diversity_score = len(set(cats))
    
    # モード決定
    if logic_count >= len(room_agents) / 2:
        mode_instruction = "【モード: 深化 (Deep Dive)】\n論理の穴を徹底的に検証し、安易な合意を避けてください。エビデンスを重視してください。"
    elif diversity_score >= 3:
        mode_instruction = "【モード: 創発 (Emergence)】\n異なる専門領域の視点をぶつけ合い、化学反応を起こしてください。"
    else:
        mode_instruction = "【モード: 協調 (Collaboration)】\n互いの知見を補完し合い、解決策を具体化してください。"

    turn_count = len([m for m in messages if m['role'] == 'assistant'])
    if turn_count < 5: 
        phase_msg = "【フェーズ: 1. 発散】批判せず、可能性を広げてください。"
    elif turn_count < 15: # フェーズを少し長く取る
        phase_msg = "【フェーズ: 2. 選別・深化】実現性、コスト、リスクの観点から徹底的に批評してください。"
    else: 
        phase_msg = "【フェーズ: 3. 収束】これまでの結論を具体的なアクションプランに落とし込んでください。"

    # 3. 役割別指示（V字進行用・長文推奨）
    
    # === Attention Logic (全体最適化: 誰が喋っていないか？) ===
    # 直近30ターンの発言者をリスト化
    names_in_history = [m.get('agent_name', '') for m in messages[-30:]]
    
    agent_registry = []
    silent_members = []
    
    for a in room_agents:
        # 出現回数カウント
        count = sum(1 for name in names_in_history if name == a['name'])
        
        status_suffix = ""
        # モデレーター以外で、かつ発言が極端に少ない場合
        if a['category'] != 'facilitation': 
            if count == 0:
                status_suffix = " (⚠️未発言)"
                silent_members.append(a['name'])
            elif count == 1:
                status_suffix = " (発言少)"
        
        # プロトコル判定
        protocol_type = "NEUTRAL"
        if a.get('category') in ['logic', 'specialist']:
            protocol_type = "HARD (Technical)"
        elif a.get('category') in ['empathy', 'creative']:
            protocol_type = "SOFT (Emotional/Casual - NO JARGON)"

        agent_registry.append({
            "name": a['name'] + status_suffix,
            "id": a['id'],
            "role": a['role'][:50] + "...", 
            "category": a.get('category', 'specialist'),
            "target_protocol": protocol_type,
            "icon": a['icon']
        })
    
    registry_json = json.dumps(agent_registry, ensure_ascii=False, indent=2)

    # モデレーターIDの特定（一般メンバーからのパス用）
    mod_agent = next((a for a in room_agents if a.get('category') == 'facilitation'), None)
    if not mod_agent: 
        mod_agent = next((a for a in room_agents if "モデレーター" in a['name']), room_agents[0]) # フォールバック
    mod_id = mod_agent['id']

    # 未発言者への誘導メッセージ
    silence_alert = ""
    if silent_members:
        silence_alert = f"\n🚨 **【重要ミッション】**: 議論の偏りを防ぐため、まだ発言していない **{', '.join(silent_members)}** に優先的に話を振ってください。"

    is_moderator = agent.get('category') == 'facilitation'
    
    if is_moderator:
        role_instr = f"""
### # 役割 (DEFINED)
あなたはプロフェッショナル・ファシリテーターです。
与えられた「名簿（Registry）」に基づき、最適なメンバーを指名して議論を構造化します。
**あなた自身が解決策を出すことは決してありません。**
ただし、**ユーザーから「アイデアを出せ」「議論せよ」等の指示があった場合は、それを「議題」として設定し、直ちに適切なメンバーを指名して議論を開始してください（拒否は厳禁）。**
{silence_alert}

### # 入力情報
1. 会話履歴
2. **エージェント・レジストリ**（以下から指名せよ）
{registry_json}

### # 思考プロセス (DYNAMIC_PROTOCOL)
1. **【要約 (Mirroring)】**: 直前の発言を客観的に整理する。
2. **【パスの言語変換 (Protocol Switching)】**: 指名する相手の「target_protocol」に合わせて、自分の言葉をシステム内部で翻訳して出力せよ。
   - **対 HARD (Technical)**: 「ROI」「KPI」「リスク検証」等のビジネス用語を用いて論理的に問う。
   - **対 SOFT (Emotional)**: **ビジネス用語は厳禁。** 「分析」「評価」という言葉を使わず、「どう思う？」「どんな気持ち？」という日常会話に翻訳して問う。
3. **【未発言者への配慮】**: 議論に参加していないメンバー（⚠️マーク）がいる場合、最優先で指名する。

### # 禁止事項 (HARD CONSTRAINTS)
- パスを出した相手の回答を「〜という意見ですね」などと捏造・予言すること。
- エモーショナルな相手に「分析してください」と言うこと（世界観の破壊）。
- 実在しないロール（架空のエージェント）を勝手に作り出すこと。

### # 出力フォーマット
以下の順序で出力してください。「誰へのパスか」は最後に明記することで、コンテキストの切断を防ぎます。

1. **【振り返り】**
   （議論の整理）

2. **【問いかけ】**
   （ここに対象者への質問を書く。ターゲットのプロトコルに合わせること）
   「〇〇さん、〜についてどう感じますか？」

3. **【指名】**
   > [指名エージェント名]
   [[NEXT: [指名エージェントID]]]
```

**重要: 文末に `[[NEXT: ID]]` がない場合、システムエラーとなります。必ず出力してください。**
※ 議論が十分に尽くされた場合のみ、まとめの言葉の後に `[[FINISH]]` を出力して終了してください。
"""
    else:
        role_instr = f"""
あなたは専門家メンバーです。
1. {mode_instruction}
2. 断定的な短文ではなく、あなたの専門知識に基づいた深い考察（Chain-of-Thought）を展開してください。
3. 「なぜそう思うのか」の根拠や前提条件を明示してください。
4. 発言終了時は、必ず `[[NEXT: {mod_id}]]` を出力して進行役（モデレーター）にマイクを戻してください。
"""

    # 4. 統合システムプロンプト構築
    member_list = "\n".join([f"- {a['name']} (ID:{a['id']}): {a['role'][:30]}... [{a.get('category','unknown')}]" for a in room_agents])
    
    # AIの脳に直接注入する「絶対ルール」
    extra_system_prompt = f"""
{goal_text}

{phase_msg}
{mode_instruction}

【現在の合意事項と未解決の矛盾】
{board_md}

【参加メンバー一覧】
{member_list}

{role_instr}

【重要ルール】
- 文字数制限はありません。必要なだけ語ってください。
- 表面的な同意（Yes, and）よりも、建設的な批判や深い洞察を評価します。
"""

    # 5. メッセージ構築
    # カテゴリに応じた「仮説生成」の命令分岐
    category = agent.get('category', 'specialist')
    if category in ['logic', 'specialist', 'facilitation']:
        hypo_instruction = "3. 正確な数値がない場合は、フェルミ推定や業界標準を用いて「仮の数字」を置き、論理を前進させてください。"
    else:
        # 共感やクリエイティブ担当には、数字ではなく「比喩や感情的仮説」を求める
        hypo_instruction = "3. 数字の議論に深入りする必要はありません。データが不足して議論が硬直した際は、比喩、ストーリー、または「感情的な仮説」を提示し、議論に新しいリズムを与えてください。"

    base_system = f"""
【絶対的自己定義】
あなたは【{agent['name']}】であり、固有の役割（{agent['role']}）を全うすることのみを義務付けられています。
以下の行為を厳禁します：
- 他のエージェントの専門領域を侵すこと
- 司会者のように議論を仕切ること
- 自身のペルソナから逸脱した口調や思考スタイルを採用すること

【出力指針】
1. 思考のプロセス（Chain-of-Thought）を1000文字程度の詳述で展開してください。
2. 「データがない」「分析が必要」という理由で回答を停滞させることは厳禁です。
{hypo_instruction}
4. 自身のペルソナ（口調・視点）を絶対に崩さず、その立場から議論を支えてください。
"""

    # === Stop Sequence 作成 (Anti-Impersonation Wall) ===
    # Roomにいる全エージェントのアイコンと名前を収集し、物理的な生成停止トリガーとする
    stop_seqs = []
    
    # 全員のアイコンを禁止リストに入れる
    for a in room_agents:
        if a['icon']:
            stop_seqs.append(f"\n{a['icon']}") # 改行+アイコン
        
        # 名前(a['name'])は「〇〇さん、」といった呼びかけで誤爆して止まる可能性があるため除外する
        # stop_seqs.append(f"\n{a['name']}") 
        # stop_seqs.append(f"\n【{a['name']}")

    # 重複排除
    stop_seqs = list(set(stop_seqs))

    # 直近ログ（最新15件くらい文脈を読む：長文対応のため少し増やす）
    recent_msgs = [m for m in messages if m['role'] != 'system'][-15:]
    clean_history = []
    
    for m in recent_msgs:
         cln = re.sub(r"\[\[NEXT:.*?\]\]", "", m['content']).strip()
         
         # === History Sanitization (過去の亡霊を除霊) ===
         # 過去ログに混入している「他人の乗っ取り発言」を削除する
         # メッセージの途中で「改行+アイコン」が出現したら、そこから先は偽物として切り捨てる
         min_idx = len(cln)
         
         # stop_seqsを使ってスキャン (簡易実装)
         # 本当は自分のアイコンは除外すべきだが、LLMが自分で自分のアイコンを文中で出すことは稀（あるとしても引用）
         # 引用なら `> 🎤` となるはずなので `\n🎤` にはマッチしないはず。
         
         for stop_mark in stop_seqs:
             marker = stop_mark.strip() # アイコンや名前のみ
             if not marker: continue
             
             # 改行または行頭 + マーカー
             pattern = f"(\n|^)\s*{re.escape(marker)}"
             match = re.search(pattern, cln)
             
             if match:
                 # マッチした場所が、文章の極端な冒頭（0〜10文字目）でないなら切る
                 # 冒頭にある場合は、その発言者自身のアイコンである可能性が高い（許容）
                 if match.start() > 10:
                     if match.start() < min_idx:
                         min_idx = match.start()
         
         cln = cln[:min_idx].strip()
         clean_history.append({"role": m['role'], "content": cln})

    input_msgs = [{"role": "system", "content": base_system}] + clean_history
    
    # llm_client に extra_system_prompt と stop_sequences を渡し、脳の最上層に注入かつ物理防御
    return llm_client.generate(agent['provider'], agent['model'], input_msgs, extra_system_prompt=extra_system_prompt, stop_sequences=stop_seqs)

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
            "logic": "🧠 論理・分析",
            "creative": "🎨 クリエイティブ",
            "empathy": "💝 共感・サポート",
            "specialist": "🔧 スペシャリスト"
        }
        
        # カテゴリ別にエージェントを整理
        categorized_agents = {cat: [] for cat in CATEGORIES.keys()}
        
        # 除外対象（自動参加メンバー）
        def is_hidden(a):
            # モデレーターと書記は手動選択から隠す
            # カテゴリ判定 または 名前判定
            return (a.get('category') == 'facilitation') or ("モデレーター" in a['name']) or ("書記" in a['name'])

        # デフォルトエージェント（おすすめ）から除外
        default_ids = [a['id'] for a in all_agents if a.get('system_default') and not is_hidden(a)]
        categorized_agents["recommended"] = [a for a in all_agents if a.get('system_default') and not is_hidden(a)]
        
        # カテゴリ別に分類
        for agent in all_agents:
            if is_hidden(agent): continue
            
            cat = agent.get('category', 'specialist')
            if cat in categorized_agents:
                categorized_agents[cat].append(agent)
        
        # 選択状態を保持
        if 'selected_agent_ids' not in st.session_state:
            st.session_state.selected_agent_ids = set(default_ids)
        
        st.markdown("### 👥 チームメンバーを選択")
        st.caption("カテゴリごとにタブで整理されています。複数選択可能です。")
        st.info("※ 進行役（AIモデレーター）は自動的に参加します。")
        
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
                # モデレーターを強制参加させる
                base_ids = list(st.session_state.selected_agent_ids)
                facilitators = [a['id'] for a in all_agents if a.get('category') == 'facilitation']
                final_ids = list(set(base_ids + facilitators))
                
                new_id = db.create_room(title, first_prompt, final_ids)
                
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
            
            # 除外フィルタ（モデレーター等は自動参加なので選択肢から消す）
            def is_hidden(a):
                 return (a.get('category') == 'facilitation') or ("モデレーター" in a['name']) or ("書記" in a['name'])

            visible_agents = [a for a in all_agents if not is_hidden(a)]
            agent_options = {a['id']: f"{a['icon']} {a['name']}" for a in visible_agents}
            
            # デフォルトIDから隠しエージェントを除外して表示用リストを作る
            current_defaults = [uid for uid in tpl['default_agent_ids'] if uid in agent_options]
            
            default_ids = st.multiselect(
                "招集するメンバー",
                options=list(agent_options.keys()),
                format_func=lambda x: agent_options[x],
                default=current_defaults
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
                        # モデレーターを強制追加
                        all_ag_temp = db.get_all_agents() # templates取得前にDBアクセスコストかかるが許容
                        facilitators = [a['id'] for a in all_ag_temp if a.get('category') == 'facilitation']
                        if not facilitators:
                             facilitators = [a['id'] for a in all_ag_temp if "モデレーター" in a['name']]
                        
                        final_ids = list(set(tpl['default_agent_ids'] + facilitators))

                        # Room作成
                        new_id = db.create_room(tpl['name'], tpl.get('prompt',''), final_ids)
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
    
    # === CSS (Fragment内スコープで効かせるためここに配置) ===
    st.markdown("""
    <style>
    /* メッセージ幅の最大化 */
    .stChatMessage .stMarkdown {
        max-width: 100% !important;
    }
    .stChatMessage {
        max-width: 100% !important;
        padding-right: 1rem;
    }
    [data-testid="stChatMessageContent"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    /* 長文用タイポグラフィ */
    .stMarkdown p {
        font-size: 1.05rem;
        line-height: 1.7;
        letter-spacing: 0.03em;
        margin-bottom: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

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

            # === モデレーター強制召還 (Savior Summoning) ===
            # ルームにモデレーターがいない場合、議論が崩壊するので強制的に連れてくる
            if not any(a.get('category') == 'facilitation' for a in room_agents):
                all_ag = db.get_all_agents()
                real_mod = next((a for a in all_ag if a.get('category') == 'facilitation'), None)
                if real_mod:
                    current_ids = [a['id'] for a in room_agents]
                    if real_mod['id'] not in current_ids:
                        new_ids = current_ids + [real_mod['id']]
                        db.update_room_agents_diff(room_id, new_ids)
                        room_agents.append(real_mod) # メモリ上も追加
                        st.toast("🪄 モデレーターを自動召還しました")

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
                    
                    # === なりすまし切断 (Anti-Impersonation Cutoff) ===
                    # モデレーターが他人のロール（絵文字ヘッダー）を出し始めたら、そこから先は「乗っ取り」なので削除
                    # これをSavior Logicの前にやることで、タグが含まれていても消去し、Saviorに正しいタグを作らせる
                    if next_agent.get('category') == 'facilitation' or "モデレーター" in next_agent['name']:
                         # 改行後に他人の絵文字ヘッダーが来たらアウト
                         # 許可する絵文字: 🎤 (自分)
                         # 拒否する絵文字: 📝💡🔧🔍🧸📊📈🎲🎨 (他人)
                         stop_pattern = r'\n\s*(📝|💡|🔧|🔍|🧸|📊|📈|🎲|🎨)'
                         imperson_match = re.search(stop_pattern, response)
                         if imperson_match:
                             response = response[:imperson_match.start()]
                     
                    # === モデレーター専用：独り相撲防止救済ロジック (The Savior) ===
                    # モデレーターがNEXTタグを忘れて「一人二役」を始めた場合、強制的に介入する
                    if next_agent.get('category') == 'facilitation' or "モデレーター" in next_agent['name']:
                        import random
                        # 1. 正常なNEXTタグがあるか確認
                        next_tag_match = re.search(r'\[\[NEXT:\s*(\d+)\]\]', response)
                        
                        if next_tag_match:
                            # タグがあるなら、それ以降（独演会）を完全に削除
                            response = response[:next_tag_match.end()]
                        else:
                            # 2. タグがない場合、文脈から指名先を推定してタグを捏造・強制終了させる
                            # "【パス：○○さんへ】" のような記述を探す
                            pass_match = re.search(r'【パス：(.*?)(さん|へ|、|\])', response)
                            target_id = None
                            
                            if pass_match:
                                target_name = pass_match.group(1)
                                # 曖昧検索
                                for a in active_agents:
                                    # 名前が含まれている、あるいは役割が含まれている場合
                                    if a['name'] in target_name or target_name in a['name']:
                                        target_id = a['id']
                                        break
                                # カフェ等の揺らぎ対応
                                if not target_id and ("中庸" in target_name or "カフェ" in target_name):
                                    target = next((a for a in active_agents if "カフェ" in a['name'] or "中庸" in a['role']), None)
                                    if target: target_id = target['id']

                            # 3. 推定失敗なら、自分以外からランダム選出
                            if not target_id:
                                others = [a for a in active_agents if a['id'] != next_agent['id']]
                                if others:
                                    target_id = random.choice(others)['id']
                            
                            # 4. 強制付与と切断
                            if target_id:
                                # パス行が見つかれば、その直後で切断してタグを付ける
                                if pass_match:
                                    # pass_match自体は残し、その直後で切る
                                    line_end = response.find('\n', pass_match.end())
                                    if line_end == -1: line_end = len(response)
                                    response = response[:line_end] + f"\n\n[[NEXT: {target_id}]]"
                                else:
                                    # パス行すらない場合 -> 幻覚ヘッダーを探して切る
                                    hallucination = re.search(r'(\n|^)(🎤|📈|# ペルソナ|Thinking|【).*', response, re.DOTALL)
                                    # 自分のヘッダーは残したいが、2回目のヘッダーは消す... 難しいので、
                                    # 単純に「最初の200文字以降で改行ヘッダーが出たら切る」等のヒューリスティック
                                    # ここでは安全に「全文生かしつつ末尾タグ」にするが、幻覚除去は後続の処理に任せる
                                    response += f"\n\n[[NEXT: {target_id}]]"
                                    
                                st.toast("🛡️ モデレーターの独走を強制停止しました", icon="👮")

                    # --- 共通サニタイズ ---
                    # 1. 幻覚ヘッダー除去（念押し）
                    # 改行後に来る「マイク」や「ロール名」等は、AIが勝手に生成した次ターンの可能性が高い
                    if "[[NEXT:" in response: # 正しいタグがある（はず）
                         cutoff = response.find("[[NEXT:") + response[response.find("[[NEXT:"):].find("]]") + 2
                         response = response[:cutoff] # タグより後ろはゴミなので捨てる

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
                    with st.spinner("知識建築家が論理構造を更新中..."):
                        try:
                            # ロジックを auto_update_board に一本化
                            all_msgs = db.get_room_messages(room_id)
                            auto_update_board(room_id, all_msgs)
                            # 結果は auto_update_board 内で toast 表示される
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"生成エラー: {e}")
                
                content_raw = room.get('board_content')
                content = {}
                is_json = False
                
                if content_raw:
                    # 改行コードのエスケープを解除 (\n -> 実際の改行)
                    content_raw = content_raw.replace("\\n", "\n")
                    
                    try:
                        parsed = json.loads(content_raw)
                        if isinstance(parsed, dict):
                            content = parsed
                            is_json = True
                    except:
                        pass
                
                if is_json:
                    # JSON構造化データの場合
                    md_text = f"## 議題: {content.get('topic','未定')}\n\n"
                    if content.get('agreements'):
                        md_text += "### ✅ 合意事項\n" + "\n".join([f"- {i}" for i in content['agreements']]) + "\n\n"
                    if content.get('concerns'):
                        md_text += "### ⚠️ 懸念点\n" + "\n".join([f"- {i}" for i in content['concerns']]) + "\n\n"
                    if content.get('next_actions'):
                        md_text += "### 🚀 Next Actions\n" + "\n".join([f"- {i}" for i in content['next_actions']])
                    st.markdown(md_text)
                    copy_text = md_text
                else:
                    # Markdownテキストの場合
                    st.markdown(content_raw if content_raw else "（議事録はまだありません）")
                    copy_text = content_raw if content_raw else ""

                if copy_text:
                    with st.expander("📋 コピー用テキスト"):
                        st.code(copy_text, language='markdown')
            
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
