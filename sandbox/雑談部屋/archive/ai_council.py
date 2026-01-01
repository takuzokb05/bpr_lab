"""
AI Council (AI評議会) - Multi-Agent Discussion System
複数のAIエージェントが議論を行い、リアルタイムで議事録を生成するシステム
"""

import streamlit as st
import openai
import anthropic
import google.generativeai as genai
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')
from typing import List, Dict, Optional
import json
import time
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="AI Council - AI評議会",
    page_icon="💀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    /* 全体のダークモード基調 */
    .main {
        background-color: #0e1117;
    }
    
    /* 左サイドバー - 作戦司令室 */
    .css-1d391kg {
        background-color: #1a1d24;
    }
    
    /* エージェントカード */
    .agent-card {
        background: linear-gradient(135deg, #1e2530 0%, #2a2f3d 100%);
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        border-left: 4px solid;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    .agent-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    }
    
    /* 議論アリーナ - メッセージ */
    .message-bubble {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        border-left: 4px solid;
        animation: fadeIn 0.5s ease-in;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
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
    
    /* スケルトンローディング */
    .skeleton {
        background: linear-gradient(90deg, #2d3748 25%, #4a5568 50%, #2d3748 75%);
        background-size: 200% 100%;
        animation: loading 1.5s ease-in-out infinite;
        border-radius: 8px;
        height: 20px;
        margin: 8px 0;
    }
    
    @keyframes loading {
        0% {
            background-position: 200% 0;
        }
        100% {
            background-position: -200% 0;
        }
    }
    
    /* ライブボード - ハイライト効果 */
    .highlight-update {
        background-color: rgba(255, 215, 0, 0.2);
        animation: highlight 2s ease-out;
        border-radius: 4px;
        padding: 2px 4px;
    }
    
    @keyframes highlight {
        0% {
            background-color: rgba(255, 215, 0, 0.4);
        }
        100% {
            background-color: transparent;
        }
    }
    
    /* ボタンスタイル */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* 緊急停止ボタン */
    .stop-button {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
    }
    
    .stop-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(220, 38, 38, 0.6);
    }
    
    /* API接続ステータス */
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        animation: pulse 2s ease-in-out infinite;
    }
    
    .status-online {
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }
    
    .status-offline {
        background-color: #ef4444;
        box-shadow: 0 0 8px #ef4444;
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    /* ツールチップ */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        background-color: #1f2937;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px 12px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -60px;
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# エージェント定義
AGENTS = {
    "facilitator": {
        "name": "🎤 AIモデレーター",
        "color": "#8b5cf6",
        "role": "知的で冷静な女性ニュースキャスター。物腰は柔らかいが進行管理は鉄壁。丁寧語で話し、各発言を要約してから次の発言者を指名する。議論が脱線したら「お話の途中ですが、テーマに戻りましょう」と笑顔で軌道修正する。",
        "model": "chatgpt-4o-latest",
        "provider": "openai"
    },
    "logic": {
        "name": "📐 論理担当",
        "color": "#3b82f6",
        "role": "リスク管理の番人。「予算は？」「法律は？」「実現可能性は？」と常に疑う。数字とエビデンスを要求する。",
        "model": "chatgpt-4o-latest",
        "provider": "openai"
    },
    "idea": {
        "name": "👽 アイデア",
        "color": "#10b981",
        "role": "空気を読まない天才。実現性は無視して、水平思考（ラテラルシンキング）で別角度のボールを投げる。",
        "model": "gemini-3-flash-preview",
        "provider": "google"
    },
    "empathy": {
        "name": "❤️ 共感担当",
        "color": "#ec4899",
        "role": "ユーザーの代弁者。「それは便利だけど、ユーザーは疲れませんか？」「誰も傷つきませんか？」と感情面をケアする。",
        "model": "claude-sonnet-4-20250514",
        "provider": "anthropic"
    },
    "scribe": {
        "name": "📝 書記",
        "color": "#6b7280",
        "role": "透明な記録者（UIには出ない）。会話の文脈を読み解き、構造化する能力に特化。",
        "model": "claude-sonnet-4-20250514",
        "provider": "anthropic"
    }
}

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "board_content" not in st.session_state:
    st.session_state.board_content = {
        "topic": "",
        "current_point": "",
        "agreements": [],
        "concerns": [],
        "next_actions": []
    }
if "active_agents" not in st.session_state:
    st.session_state.active_agents = {
        "facilitator": True,
        "logic": True,
        "idea": True,
        "empathy": True,
        "scribe": True
    }
if "discussion_running" not in st.session_state:
    st.session_state.discussion_running = False
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {
        "openai": "",
        "google": "",
        "anthropic": ""
    }
# 討論番組の進行フェーズ管理
if "phase" not in st.session_state:
    st.session_state.phase = "opening"  # opening, divergence, convergence, conclusion
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "current_speaker" not in st.session_state:
    st.session_state.current_speaker = None

def check_api_status(provider: str) -> bool:
    """APIの接続状態をチェック"""
    try:
        if provider == "openai" and st.session_state.api_keys["openai"]:
            return True
        elif provider == "google" and st.session_state.api_keys["google"]:
            return True
        elif provider == "anthropic" and st.session_state.api_keys["anthropic"]:
            return True
    except:
        return False
    return False

def call_openai(messages: List[Dict], model: str = "gpt-4o") -> str:
    """OpenAI APIを呼び出し"""
    try:
        client = openai.OpenAI(api_key=st.session_state.api_keys["openai"])
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[エラー: {str(e)}]"

def call_google(messages: List[Dict], model: str = "gemini-3-flash-preview") -> str:
    """Google Gemini APIを呼び出し"""
    try:
        genai.configure(api_key=st.session_state.api_keys["google"])
        model_instance = genai.GenerativeModel(model)
        
        # メッセージ形式を変換
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        response = model_instance.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[エラー: {str(e)}]"

def call_anthropic(messages: List[Dict], model: str = "claude-sonnet-4-20250514") -> str:
    """Anthropic Claude APIを呼び出し"""
    try:
        client = anthropic.Anthropic(api_key=st.session_state.api_keys["anthropic"])
        
        # システムメッセージを分離
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m for m in messages if m["role"] != "system"]
        
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            system=system_msg,
            messages=user_messages
        )
        return response.content[0].text
    except Exception as e:
        return f"[エラー: {str(e)}]"

def generate_agent_response(agent_id: str, context: List[Dict]) -> str:
    """エージェントの応答を生成"""
    agent = AGENTS[agent_id]
    
    # 司会者の場合は、フェーズに応じた進行プロンプトを生成
    if agent_id == "facilitator":
        phase = st.session_state.phase
        turn_count = st.session_state.turn_count
        
        if phase == "opening":
            system_prompt = f"""あなたは{agent['name']}です。
役割: {agent['role']}

現在のフェーズ: オープニング

ユーザーがテーマを提示しました。以下の形式で議論を開始してください:

「承知いたしました。本日のテーマは『{{テーマ}}』ですね。
まずは新しい視点からアイデアを出していただきたいと思います。
アイデア担当さん、口火を切っていただけますか？」

丁寧語（です・ます調）で、落ち着いた知的な口調で話してください。"""
        
        elif phase == "divergence":
            system_prompt = f"""あなたは{agent['name']}です。
役割: {agent['role']}

現在のフェーズ: 発散（アイデア出し）

直前の発言を簡潔に要約してから、次の発言者を指名してください。

例:
「なるほど、〇〇という案ですね。
では、共感担当さん、ユーザー視点ではいかがでしょうか？」

議論が脱線しそうな場合は、「お話の途中ですが、テーマは『{{テーマ}}』です。軌道修正しましょう」と介入してください。"""
        
        elif phase == "convergence":
            system_prompt = f"""あなたは{agent['name']}です。
役割: {agent['role']}

現在のフェーズ: 収束（リスク検証と改善）

アイデアが出揃ったので、実現可能性を検証するフェーズです。

「それでは、出てきたアイデアの実現可能性を検証していきましょう。
論理担当さん、コストやリスクの観点からご意見をお願いします。」

のように、建設的な議論を促してください。"""
        
        else:  # conclusion
            system_prompt = f"""あなたは{agent['name']}です。
役割: {agent['role']}

現在のフェーズ: 結論

議論が十分に進みました。以下の形式でまとめに入ってください:

「お時間も迫ってまいりましたので、ここまでの議論をまとめたいと思います。
書記さん、最終的な議事録をお願いします。」

落ち着いた口調で、議論を締めくくってください。"""
    
    else:
        # 他のエージェントは通常のプロンプト
        system_prompt = f"""あなたは{agent['name']}です。
役割: {agent['role']}

必ず日本語で思考し、発言してください。
あなたの性格と役割に忠実に、議論に貢献してください。
簡潔で鋭い発言を心がけてください。

重要: 司会者（AIモデレーター）から指名された時のみ発言してください。
他のエージェントの発言中は黙って聞いてください。"""
    
    messages = [{"role": "system", "content": system_prompt}] + context
    
    # プロバイダーに応じてAPI呼び出し
    if agent["provider"] == "openai":
        return call_openai(messages, agent["model"])
    elif agent["provider"] == "google":
        return call_google(messages, agent["model"])
    elif agent["provider"] == "anthropic":
        return call_anthropic(messages, agent["model"])
    
    return "[エラー: 不明なプロバイダー]"

def update_board(messages: List[Dict]) -> Dict:
    """書記エージェントが議事録を更新"""
    scribe_prompt = f"""以下の議論を分析し、議事録を更新してください。

現在の議事録:
{json.dumps(st.session_state.board_content, ensure_ascii=False, indent=2)}

最新の議論:
{json.dumps(messages[-5:], ensure_ascii=False, indent=2)}

以下のJSON形式で議事録を更新してください:
{{
    "topic": "議題",
    "current_point": "現在の論点",
    "agreements": ["合意事項1", "合意事項2"],
    "concerns": ["懸念点1", "懸念点2"],
    "next_actions": ["アクション1", "アクション2"]
}}

必ず有効なJSONを返してください。"""
    
    try:
        response = call_anthropic([
            {"role": "user", "content": scribe_prompt}
        ], AGENTS["scribe"]["model"])
        
        # JSONを抽出
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        st.error(f"議事録更新エラー: {str(e)}")
    
    return st.session_state.board_content

# ========== UI構築 ==========

# 🅰️ 左ペイン：作戦司令室
with st.sidebar:
    st.title("🎯 作戦司令室")
    st.markdown("---")
    
    # APIキー設定
    with st.expander("🔑 API設定", expanded=not all(st.session_state.api_keys.values())):
        st.session_state.api_keys["openai"] = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_keys["openai"],
            type="password"
        )
        st.session_state.api_keys["google"] = st.text_input(
            "Google API Key",
            value=st.session_state.api_keys["google"],
            type="password"
        )
        st.session_state.api_keys["anthropic"] = st.text_input(
            "Anthropic API Key",
            value=st.session_state.api_keys["anthropic"],
            type="password"
        )
    
    st.markdown("### 👥 エージェント編成")
    
    # エージェントトグル
    for agent_id, agent in AGENTS.items():
        if agent_id == "scribe":  # 書記は表示しない
            continue
            
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div class="agent-card" style="border-left-color: {agent['color']}">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 24px; margin-right: 8px;">{agent['name'].split()[0]}</span>
                    <strong>{agent['name'].split()[1] if len(agent['name'].split()) > 1 else ''}</strong>
                </div>
                <div style="font-size: 12px; color: #9ca3af; margin-bottom: 4px;">
                    {agent['model']}
                </div>
                <div style="font-size: 13px; color: #d1d5db;">
                    {agent['role'][:50]}...
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.session_state.active_agents[agent_id] = st.toggle(
                "ON",
                value=st.session_state.active_agents[agent_id],
                key=f"toggle_{agent_id}",
                label_visibility="collapsed"
            )
    
    st.markdown("---")
    
    # API接続状態
    st.markdown("### 📡 API接続状態")
    for provider in ["openai", "google", "anthropic"]:
        status = check_api_status(provider)
        status_class = "status-online" if status else "status-offline"
        st.markdown(f"""
        <div style="margin: 8px 0;">
            <span class="status-dot {status_class}"></span>
            <span style="color: {'#10b981' if status else '#ef4444'}">
                {provider.upper()}: {'接続中' if status else '未接続'}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 緊急停止ボタン
    if st.button("🛑 議論を強制終了・まとめ", type="primary", use_container_width=True):
        st.session_state.discussion_running = False
        st.success("議論を終了しました")

# メインエリア（中央と右を2カラムで分割）
col_center, col_right = st.columns([1.2, 1])

# 🅱️ 中央ペイン：議論アリーナ
with col_center:
    st.title("💬 議論アリーナ")
    
    # ユーザー入力
    user_input = st.text_area(
        "議題を入力してください",
        placeholder="例: 空き家の有効活用策について、新規事業案を出せ",
        height=100,
        key="user_input"
    )
    
    if st.button("🚀 議論を開始", type="primary", disabled=st.session_state.discussion_running):
        if user_input and any(st.session_state.api_keys.values()):
            # 討論番組の新しいセッション開始
            st.session_state.discussion_running = True
            st.session_state.phase = "opening"
            st.session_state.turn_count = 0
            st.session_state.current_speaker = None
            
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            st.session_state.board_content["topic"] = user_input
            st.rerun()
    
    st.markdown("---")
    
    # メッセージ表示エリア
    message_container = st.container()
    
    with message_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="message-bubble" style="border-left-color: #8b5cf6;">
                    <div style="font-weight: bold; margin-bottom: 8px;">
                        👤 オーナー
                    </div>
                    <div>{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                agent = AGENTS.get(msg.get("agent_id", ""), {})
                st.markdown(f"""
                <div class="message-bubble" style="border-left-color: {agent.get('color', '#6b7280')};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-weight: bold;">
                            {agent.get('name', '不明')}
                        </div>
                        <div style="font-size: 11px; color: #9ca3af;">
                            {agent.get('model', '')}
                        </div>
                    </div>
                    <div>{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)

# ☪️ 右ペイン：ライブ・ボード
with col_right:
    st.title("📋 ライブ・ボード")
    
    if not st.session_state.board_content["topic"]:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); 
                    padding: 32px; border-radius: 12px; text-align: center; color: #374151;">
            <h3>✨ ここにAIたちの議論の成果がリアルタイムでまとめられます</h3>
            <p style="margin-top: 16px;">
                中央のパネルに最初のテーマを入力して、議論を始めましょう！
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        board = st.session_state.board_content
        
        st.markdown(f"## 📌 {board['topic']}")
        st.markdown("---")
        
        if board['current_point']:
            st.markdown(f"### 🎯 現在の論点")
            st.markdown(f"**{board['current_point']}**")
            st.markdown("")
        
        if board['agreements']:
            st.markdown("### ✅ 合意形成されたポイント")
            for item in board['agreements']:
                st.markdown(f"- {item}")
            st.markdown("")
        
        if board['concerns']:
            st.markdown("### ⚠️ 懸念点・リスク")
            for item in board['concerns']:
                st.markdown(f"- {item}")
            st.markdown("")
        
        if board['next_actions']:
            st.markdown("### 📝 ネクストアクション")
            for item in board['next_actions']:
                st.checkbox(item, key=f"action_{hash(item)}")

# 議論の自動進行（討論番組スタイル）
if st.session_state.discussion_running and len(st.session_state.messages) > 0:
    with st.spinner("💭 AIエージェントが思考中..."):
        turn_count = st.session_state.turn_count
        phase = st.session_state.phase
        
        # フェーズ遷移の管理
        if turn_count == 0:
            # オープニング: 司会者が議論を開始
            st.session_state.phase = "opening"
            next_speaker = "facilitator"
        
        elif turn_count == 1:
            # 発散フェーズ: アイデア担当から開始
            st.session_state.phase = "divergence"
            next_speaker = "idea"
        
        elif turn_count <= 6:
            # 発散フェーズ継続: アイデア → 共感 → 司会 のサイクル
            cycle = ["idea", "empathy", "facilitator"]
            next_speaker = cycle[(turn_count - 1) % len(cycle)]
        
        elif turn_count == 7:
            # 収束フェーズ: 司会者が移行を宣言
            st.session_state.phase = "convergence"
            next_speaker = "facilitator"
        
        elif turn_count <= 12:
            # 収束フェーズ: 論理 → アイデア → 司会 のサイクル
            cycle = ["logic", "idea", "facilitator"]
            next_speaker = cycle[(turn_count - 7) % len(cycle)]
        
        elif turn_count == 13:
            # 結論フェーズ: 司会者がまとめを宣言
            st.session_state.phase = "conclusion"
            next_speaker = "facilitator"
        
        elif turn_count < 16:
            # 最終まとめ
            next_speaker = "facilitator"
        
        else:
            # 議論終了
            st.session_state.discussion_running = False
            st.success("✅ 議論が完了しました！")
            st.rerun()
        
        # エージェントが有効かチェック
        if next_speaker in st.session_state.active_agents and st.session_state.active_agents[next_speaker]:
            # コンテキストを準備
            context = [{"role": "user", "content": msg["content"]} 
                      for msg in st.session_state.messages[-5:]]
            
            # 応答生成
            response = generate_agent_response(next_speaker, context)
            
            # メッセージ追加
            st.session_state.messages.append({
                "role": "assistant",
                "agent_id": next_speaker,
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # ターン数を増やす
            st.session_state.turn_count += 1
            st.session_state.current_speaker = next_speaker
            
            # 議事録更新（書記は常に裏で動く）
            st.session_state.board_content = update_board(st.session_state.messages)
            
            time.sleep(1)  # レート制限対策
            st.rerun()
        else:
            # エージェントが無効な場合はスキップ
            st.session_state.turn_count += 1
            st.rerun()
