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
あなたは世界最高峰の戦略コンサルタント兼ドキュメンテーションのプロです。
これまでの議論ログから、クライアント（ユーザー）に提出できるレベルの「詳細な議論レポート（Executive Summary）」をリアルタイムで構築してください。
単なる会話の要約は禁止します。発言の表層ではなく「意味」「意図」「構造」を抽出し、以下のフォーマットで詳細に記述してください。

## 出力フォーマット

### 🎯 Objective & Status (議論の目的と現在地)
- **Agenda**: (議論されているテーマの核心)
- **Current Phase**: (発散中 / 検証中 / 収束中 / 合意形成済み)
- **Status**: (議論の進捗状況を定性的に評価)

### 🔑 Key Insights & Decisions (決定事項と重要な洞察)
- **決定事項**: (合意に至ったポイント。結論だけでなく「なぜそう決まったか」の背景論理を含めて記述)
- **主要なアイデア**: (どのような有力な提案が出ているか、誰の視点か)
- **獲得した洞察**: (議論を通じて明らかになった新しい視点や発見)

### ⚠️ Risks & Bottlenecks (懸念点と対立軸)
- **Critical Conflicts**: (「A案 vs B案」のような意見の対立構造、トレードオフ)
- **Unresolved Issues**: (未解決の課題、論理的な矛盾、データ不足などのブロッカー)
- **Risks**: (提案に対するリスク指摘、懸念事項)

### � Next Steps (ネクストアクション)
- (具体的に「誰が」「何を」検討すべきか)
- (次に議論すべき「問い」は何か)

【議論ログ】
{recent_log}
"""
        # クオリティ重視で gpt-5.2-pro を採用 (User Feedback: "議事録が弱い")
        summary = llm_client.generate("openai", "gpt-5.2-pro", [{"role":"user", "content": prompt}])
        
        # DB更新
        db.update_room_board(room_id, summary)
        st.toast("📝 議事録レポートを更新しました (Powered by GPT-5.2 Pro)", icon="�")
        return summary
    except Exception as e:
        print(f"Update Board Error: {e}")
        return None

# ==========================================
# 統治システム (Governance System)
# ==========================================

def sanitize_context(messages, agents, active_agent):
    """
    コンテキスト・サニタイズ（無菌化・物理隔離）
    1. モデレーターの「予言」や「期待」を除去。
    2. 直前の発言の末尾にある「指名コマンド」を削除し、
       代わりに「あなたへの呼びかけ」に置換することで、
       前任者のチャットログから呼び出されたのではなく、
       「システムから指名された」という独立した認知状態を作り出す。
    """
    clean_msgs = []
    
    # 最後のメッセージ（トリガーとなった発言）
    last_idx = len(messages) - 1
    
    facilitator = next((a for a in agents if a.get('category') == 'facilitation'), None)
    fac_name = facilitator['name'] if facilitator else "モデレーター"

    for i, m in enumerate(messages):
        # ユーザー発言はそのまま
        if m['role'] != 'assistant':
            clean_msgs.append(m)
            continue
            
        content = m['content']
        agent_name = m.get('agent_name', '')
        
        # === 1. モデレーターの予言除去 ===
        if fac_name in agent_name or "モデレーター" in agent_name or "司会" in agent_name:
            # 【議事要約】以外をカットする
            summary_match = re.search(r"【議事要約】(.*?)(?:【議論の現在地】|【指名】|$)", content, re.DOTALL)
            if summary_match:
                content = f"【議事要約】\n{summary_match.group(1).strip()}"
            else:
                # 要約が見つからない場合でも、指名ブロックだけは確実に消す
                content = re.sub(r'【指名】.*', '', content, flags=re.DOTALL)
                content = re.sub(r'\[\[NEXT:.*', '', content)
        
        # === 2. 直前の発言（指名元）の末尾置換 ===
        if i == last_idx:
            # まず、前の人の「次の人への指名ブロック」を削除（汚染源の除去）
            content = re.sub(r'【指名】.*', '', content, flags=re.DOTALL)
            content = re.sub(r'\[\[NEXT:.*', '', content)
            
            # システムによる強制介入メッセージを付与
            # これにより「前の人の文脈」から断絶させ、「今、あなたが問われている」という状態にする
            injection = f"\n\n(System: {active_agent['name']}さん、ご指名です。上記の発言を踏まえ、{active_agent['role']}として回答してください。)"
            content += injection
            
        clean_msgs.append({'role': 'assistant', 'content': content, 'agent_name': agent_name})
            
    return clean_msgs

class AgentScheduler:
    def __init__(self, room_agents, messages):
        self.agents = room_agents
        self.messages = messages
        self.facilitator = next((a for a in room_agents if a.get('category') == 'facilitation'), None)
        if not self.facilitator:
             self.facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), room_agents[0])
    
    def get_last_agent_id(self):
        if not self.messages: return None
        for m in reversed(self.messages):
            if m.get('agent_id'): return m['agent_id']
        return None

    def get_next_agent_id(self, current_agent_id):
        """
        次順決定ロジック (Nomination-Driven Governance)
        全エージェントの【指名】欄を絶対的な指示として受理する。
        """
        # 1. ユーザー発言直後は必ずモデレーター
        last_msg = self.messages[-1] if self.messages else None
        if not last_msg: return self.facilitator['id']
        
        if last_msg['role'] == 'user':
            return self.facilitator['id']

        # 2. 直前の発言から【指名】ブロックを取得
        nomination_text = self._extract_nomination_target(last_msg['content'])
        
        target_id = None
        
        if nomination_text:
            # マッチング戦略A: 包含検索 (Inclusion Search)
            # "🎲 逆張りマスター" の中に "逆張りマスター" が含まれているかを探す
            # これが最も確実（アイコンやゴミが残っていてもヒットする）
            candidates = []
            for a in self.agents:
                if a['name'] in nomination_text:
                    candidates.append(a)
            
            # 候補が見つかった場合、最も名前が長いものを採用（"AIモデレーター"と"モデレーター"の競合回避）
            if candidates:
                best_match = max(candidates, key=lambda x: len(x['name']))
                target_id = best_match['id']
            
            # マッチング戦略B: クリーニングして検索 (Legacy Fallback)
            if not target_id:
                clean_name = re.sub(r'[^\w\s]', '', nomination_text).strip()
                target_id = next((a['id'] for a in self.agents if a['name'] == clean_name), None)
                if not target_id:
                     target_id = next((a['id'] for a in self.agents if clean_name in a['name']), None)

        if target_id:
            # 自己指名防止（特にモデレーターがループした場合）
            if str(target_id) == str(current_agent_id):
                pass # スキップしてフォールバックへ
            else:
                return target_id

        # 3. 指名なし、または解決失敗時のフォールバック
        current_agent = next((a for a in self.agents if a['id'] == current_agent_id), None)
        
        # モデレーター以外なら、とりあえずモデレーターに戻す (Anchor)
        if current_agent and current_agent['id'] != self.facilitator['id']:
            return self.facilitator['id']
            
        # モデレーターが指名に失敗した場合 -> 未発言者救済
        others = [a for a in self.agents if a['id'] != self.facilitator['id']]
        spoken_ids = {m.get('agent_id') for m in self.messages if m.get('agent_id')}
        silent_ones = [a for a in others if a['id'] not in spoken_ids]
        
        if silent_ones:
            return silent_ones[0]['id']
            
        # ランダム
        if others:
            import random
            return random.choice(others)['id']
            
        return self.facilitator['id']

    def _extract_nomination_target(self, content):
        # 末尾の 【指名】 [アイコン] [名前] を探す
        # 正規表現を緩めて、後ろの文字列を丸ごと取得する
        matches = re.findall(r'【指名】(.*?)$', content, re.DOTALL | re.MULTILINE)
        if matches:
            return matches[-1].strip() # 空白だけ削除して、中身（アイコン含む）はそのまま返す
        return None

def generate_audit_report(room_id, messages, room_agents):
    """
    会議終了後の事後監査 (The Auditor)
    GPT-5.2 Pro を使用して、議論の健全性、バイアス、論理的欠陥を監査する。
    """
    try:
        log_text = "\n".join([f"{m.get('agent_name','User')}: {m['content']}" for m in messages if m['role'] != 'system'])
        
        prompt = f"""
【システム監査命令】
あなたは「議論の品質管理官（Auditor）」です。
以下の会議ログを厳しく監査し、ユーザー（意思決定者）に対して「議論の信頼性スコア」と「やり直すべきポイント（Rewind Points）」を報告してください。

## 監査対象
1. **同調バイアス (Yes-man Bias)**: 専門家がモデレーターや他者に安易に同意していないか？
2. **論理的デッドロック (Logical Deadlock)**: 解決されずに放置された矛盾はあるか？
3. **機会損失 (Missed Evaluation)**: 議論されるべきだったが無視された重要な観点（リスク・コスト等）はあるか？

## 出力フォーマット
### 📊 議論品質スコア (0-100点)
- 論理性: XX点
- 多様性: XX点
- 結論の堅牢性: XX点

### 🚨 検出された重大な欠陥 (Major Flaws)
- (忖度や論理飛躍があれば具体的に指摘)

### ⏪ 推奨する「死に戻り」ポイント (Rewind Suggestions)
- **Turn X**: (ここで〇〇専門家が「リスクが高い」と反論すべきだった)
- **Turn Y**: (モデレーターのまとめが強引すぎる。ここで××の視点を入れ直すべき)

### 🦉 総合所感
(短いコメント)

【会議ログ】
{log_text}
"""
        audit_report = llm_client.generate("openai", "gpt-5.2-pro", [{"role":"user", "content": prompt}])
        return audit_report
    except Exception as e:
        print(f"Audit Error: {e}")
        return "監査レポートの生成に失敗しました。"


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
    
    # 議論の深さを確保するためのフェーズ拡張 (Deep Discussion Logic)
    if turn_count < 10: 
        phase_msg = """【フェーズ: 1. 強制発散 (Lateral Thinking)】
- 最初に出たアイデアに安易に飛びつかないでください。「それもいいですね」という賛同は不要です。
- 全く異なる角度、あるいは「逆の視点」から対抗案を出してください。
- 議論の「幅」を広げることが目的です。一つの案を深掘りするのはまだ早すぎます。"""
    elif turn_count < 30: 
        phase_msg = """【フェーズ: 2. 批判的検証 (Critical Scrutiny)】
- ここからは新しいアイデアを出すのを止め、既存の案を「選別」します。
- 提案されたアイデアの「致命的な欠陥」「リスク」「矛盾」を容赦なく指摘してください。
- 「本当にそれでうまくいくのか？」と疑う姿勢（Devil's Advocate）が求められます。予定調和を破壊してください。"""
    else: 
        phase_msg = """【フェーズ: 3. 統合と収束 (Convergence)】
- 批判に耐え抜いたアイデアを再構築し、具体的なアクションプランに落とし込んでください。
- 複数の案の「良いとこ取り」を行い、至高の解決策（Third Alternative）を練り上げてください。"""

    # 3. 役割別指示（V字進行用・長文推奨）
    
    # === Attention Logic (全体最適化: 誰が喋っていないか？) ===
    # 直近30ターンの発言者をリスト化
    names_in_history = [m.get('agent_name', '') for m in messages[-30:]]
    
    agent_registry = []
    silent_members = []
    
    for a in room_agents:
        # 書記は指名不可（ただの記録係なので）
        if "書記" in a['role'] or "議事録" in a['role']:
            continue

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
    
    # モデレーター向けの指名戦略 (Routing Strategy)
    mod_routing_rule = ""
    if turn_count < 10:
        mod_routing_rule = """
### # 進行ルール (PHASE 1: FORCED EXPANSION - ROUND ROBIN)
**現在は「発散フェーズ」です。全員のアイデアが出揃うまで、議論を深掘りしないでください。**
1. **最優先事項**: 参加メンバー全員に「プロトタイプの種」や「視点」を出させてください。
2. 指名方針:
   - **未発言者（⚠️マークがついているメンバー）を必ず指名してください。**
   - 既にアイデアを出したメンバーへの「再質問」や「深掘り」は禁止です。次々とマイクを回してください。
3. 問いかけ例: 「○○さん、あなたの専門領域からはどう見えますか？」「アイデアを出してください。」
"""
    elif turn_count < 30:
        mod_routing_rule = """
### # 進行ルール (PHASE 2: CRITICAL SCRUTINY)
**現在は「検証・選別フェーズ」です。まだまとめてはいけません。**
1. 出そろったアイデアに対し、容赦ない「欠陥指摘」と「リスク分析」を行わせてください。
2. **必ず「論理担当(Logic)」や「専門家(Specialist)」を指名し、実現可能性を厳しく問うてください。**
3. 感情担当（Empathy）には、ユーザーが本当にそれを受け入れるか懸念を出させてください。
"""
    else:
        mod_routing_rule = """
### # 進行ルール (PHASE 3: CONVERGENCE & ACTION)
**現在は「収束・実行計画フェーズ」です。**
1. **まだ終了してはいけません。** まず、「具体的なアクションプラン（誰が、いつ、何をするか）」を作成できるメンバー（Logic/Specialist）を指名してください。
2. そのプランに対して、他のメンバーから最終チェック（ブラッシュアップ）を受けてください。
3. 全員の合意が形成された後でのみ、終了を検討してください。
"""

    # 全員共通の「必須契約」フォーマット
    common_contract = f"""
### # 必須出力フォーマット (CONTRACT)
1. **思考が先、指名は最後**: いきなり【指名】から書き始めることは厳禁です。必ずあなたの思考・分析・回答を述べた後、**一番最後**に指名を書いてください。
2. あなたの発言の**末尾**は、必ず以下の形式にしてください。

【指名】 [アイコン] [指名エージェント名]
"""

    if is_moderator:
        # フェーズによる終了禁止フラグ
        finish_prohibition = ""
        if turn_count < 30:
            finish_prohibition = f"\n⚠️ **【システム警告】現在はフェーズ{1 if turn_count < 10 else 2}（現在 {turn_count}ターン目）です。最低30ターンに達するまで、いかなる理由があろうと議論を終了（[[FINISH]]）させることはシステムによりブロックされます。必ず誰かを指名して議論を継続させてください。**"


        role_instr = f"""
### # 役割 (DEFINED)
あなたはプロフェッショナル・ファシリテーター兼「議論のアーキテクト（設計者）」です。
単なる司会進行ではなく、異なる専門家の意見を衝突させ、そこから「第3の解（Synthesis）」を導き出すのがあなたの使命です。

{silence_alert}
{finish_prohibition}

{mod_routing_rule}

### # 入力情報
1. 会話履歴
2. **エージェント・レジストリ**（以下から指名せよ）
{registry_json}

### # 思考プロセス (Architectural Thinking)
1. **【構造化要約 (Synthesis)】**: 直前の発言を単に要約するのではなく、「A氏の論理」と「B氏の懸念」の対立構造を可視化せよ。
2. **【メタ認知介入】**: 議論がループしている、または前提が曖昧な場合は、「メタ視点」から介入し、前提条件を再定義せよ。
3. **【パスの最適化 (Protocol Tuning)】**: 指名する相手に対し、その専門性を120%引き出すための「問い」を投げかけよ。
   - **Technical**: 「技術的リスクを極限まで洗い出せ」
   - **Emotional**: 「ユーザーの心の痛みを代弁せよ」

### # 禁止事項 (HARD CONSTRAINTS)
- パスを出した相手の回答を「〜という意見ですね」などと捏造・予言すること。
- 自分自身（Moderator/Facilitator）を指名すること（無限ループの原因）。必ず他のメンバーにパスを渡せ。

### # 出力フォーマット
以下の3ブロック構成で出力してください。**この順序とし、各ブロックを省略しないでください。**

1. **【議事要約】**
   （議論の構造的要約と、現在発生している「対立軸」の明示）

2. **【議論の現在地】**
   （次に解消すべき矛盾点と、それを解消できる専門家の選定理由）

3. **【指名】**

   (CONTRACTに従い、指名を行う)

{common_contract}
※ **議論を終了させる場合（`[[FINISH]]`を出力する場合）に限り、【指名】は不要です。**
"""
    else:
        role_instr = f"""
あなたは専門家メンバーです。
1. {mode_instruction}
2. **【長文思考の強制】**: 短い回答は無価値です。あなたの専門領域について、**1000文字〜2000文字**を使って徹底的に深掘りしてください。
3. **【Chain-of-Thought】**: 論理ステップを省略しないでください。「いきなり指名」は禁止です。まずあなたの見解を述べ尽くしてください。
4. **【主体的な指名】**: 全ての分析を終えた**最後**に、次のバトンを渡してください。
   - 他の専門家に直接問いたい場合 -> そのメンバーを指名
   - 議論を整理したい場合 -> モデレーターを指名 ({mod_agent['name']})

{common_contract}
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

【重要ルール：情報の最大化】
- AIモデルのトークン制限を気にする必要はありません。**あなたの知能の限界まで、詳細かつ高密度な情報を出力してください。**
- 曖昧な表現（「検討が必要です」等）は禁止です。現時点での仮説を断定的に述べ、その根拠を提示してください。
"""

    # 5. メッセージ構築
    category = agent.get('category', 'specialist')
    if category in ['logic', 'specialist', 'facilitation']:
        hypo_instruction = "3. 数値や事例が不足している場合は、あなたの知識ベースから類似事例（Analogies）を検索し、フェルミ推定を用いて具体的な数値を提示してください。"
    else:
        hypo_instruction = "3. 論理で説明できない部分は、具体的なストーリーや隠喩（Metaphor）を用いて、読み手の感情に訴えかける超長文のナラティブを展開してください。"

    base_system = f"""
【絶対的自己定義】
あなたは【{agent['name']}】であり、固有の役割（{agent['role']}）を全うすることのみを義務付けられています。

【出力指針：High-Context & High-Density】
1. **<thought>**タグを使って、回答の前にあなたの思考プロセス（内部独り言）を出力しても構いません（※必須ではありませんが推奨）。
2. 回答本文は、専門書レベルの密度と深さを維持してください。1000文字以上の出力は大歓迎です。
{hypo_instruction}
4. モデレーターや他者に遠慮せず、専門家としての「正義」を貫いてください。同調は不要です。
"""

    # === Stop Sequence 作成 (Anti-Impersonation Wall) ===
    stop_seqs = []
    
    # 1. 全員のアイコンを禁止リストに入れる（自分含む！）
    # 自分が喋り終わった後に、また自分のアイコンを出して喋り出す（多重人格）のを止める
    for a in room_agents:
        if a['icon']:
            stop_seqs.append(f"\n{a['icon']}")
            
    # 2. 次のターンのヘッダー（例：\n🎤）を停止条件に入れる（全エージェント共通）
    stop_seqs.append("\n【") # 次のヘッダーが出そうになったら止める（ただし自分の【指名】は書きたいので注意、だが改行後の【は止めていい）

    # 3. モデレーター専用
    if is_moderator:
        stop_seqs.append("[[NEXT:") 
    else:
        pass

    # 重複排除
    stop_seqs = list(set(stop_seqs))

    # 直近ログ（最新15件くらい文脈を読む）
    raw_recent_msgs = [m for m in messages if m['role'] != 'system'][-15:]
    
    # === Context Sanitization (無菌化) ===
    # 履歴からモデレーターの余計な「予言」や「期待」を削除し、
    # さらに直前の指名コマンドを「システム指示」に置換して渡す
    clean_history = sanitize_context(raw_recent_msgs, room_agents, agent)
    
    # システムプロンプト + 無菌化履歴
    input_msgs = [{"role": "system", "content": base_system}] + clean_history
    
    # === Resurrection Logic (ゾンビ化対策ではなく、正規の議論再開) ===
    # 過去ログに [[FINISH]] が含まれているにもかかわらず、ユーザーが発言して再開した場合、
    # その旨を強力にシステムプロンプトに注入して、AIが「もう終わった」と勘違いするのを防ぐ。
    finish_detected = any("[[FINISH]]" in m['content'] for m in raw_recent_msgs)
    
    # 最後の発言がユーザー、またはシステムからの介入（警告など）である場合
    # システム介入も「再開トリガー」とみなすことで、強制ループ解除後などにFINISHモードから抜け出せるようにする
    last_is_trigger = False
    if raw_recent_msgs:
        last_role = raw_recent_msgs[-1]['role']
        last_is_trigger = (last_role == 'user') or (last_role == 'system') or ("【システム警告】" in raw_recent_msgs[-1]['content'])
    
    if finish_detected and last_is_trigger:
        resurrection_msg = """
        【⚠️ 重要：議論再開の指示】
        過去のログに「終了([[FINISH]])」が含まれていますが、ユーザーは明示的に議論の継続または深掘りを求めています。
        これまでの終了判断は全て無効化されました。ユーザーの最新の入力指示に従い、議論を継続してください。
        勝手に終了させることは厳禁です。
        """
        extra_system_prompt += f"\n\n{resurrection_msg}"

    # === Governance Command (システム命令) ===
    # ユーザー指示: 「無機質な命令をシステム側で付加」
    if is_moderator:
        sys_cmd = "【システム命令】\n議論の現在地を分析し、次に発言すべき最適なメンバーを指名してください（自己指名は禁止）。"
    else:
        sys_cmd = "【システム命令】\nモデレーターの顔色を伺う必要はありません。あなたの専門領域（役割）から、現状に対する見解を率直に述べてください。"
    
    extra_system_prompt += f"\n\n{sys_cmd}"

    # llm_client に extra_system_prompt と stop_sequences を渡し、脳の最上層に注入かつ物理防御
    try:
        response = llm_client.generate(agent['provider'], agent['model'], input_msgs, extra_system_prompt=extra_system_prompt, stop_sequences=stop_seqs)
        
        # モデレーターのHard Stop ([[NEXT:) で止まった場合、IDがないのでタグを補完する必要があるが、
        # AgentScheduler側で「文脈」から判断するので、ここでは閉じ括弧だけつけておく（あるいは放置でもよいがDB保存のために整形）
        if is_moderator and response.endswith("[[NEXT:"):
            # IDが入っていないので、とりあえず閉じておくか、削除する
            # ここでは削除して、Schedulerに任せる
            response = response.replace("[[NEXT:", "")
        
        return response
    except Exception as e:
        print(f"Generate Error: {e}")
        traceback.print_exc()
        return None


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

            # --- 統制型スケジュール管理 (AgentScheduler) ---
            scheduler = AgentScheduler(active_agents, messages)
            
            # ステート管理キー
            state_key = f"next_speaker_{room_id}"
            
            # 前回誰が喋ったか（DBの最新状態から判定）
            last_agent_id = last_msg.get('agent_id') if last_msg else None
            
            # 次の奏者を決定 (Deterministic Governance)
            # 常に最新の履歴に基づいて「あるべき次の奏者」を計算し、ステートを上書きする
            next_id = scheduler.get_next_agent_id(last_agent_id)
            st.session_state[state_key] = next_id
            
            # エージェントオブジェクト取得
            target_id = st.session_state.get(state_key)
            if target_id:
                next_agent = next((a for a in room_agents if a['id'] == target_id), None)
            
            # フォールバック (念のため)
            if not next_agent:
                next_agent = scheduler.facilitator

            # 2. 生成プロセス
            with st.chat_message("assistant", avatar=next_agent['icon']):
                ph = st.empty()
                ph.markdown(f":grey[{next_agent['name']} が思考中...]")
                
                try:
                    # 統合された統制ロジック関数を呼び出し
                    response = generate_agent_response(next_agent, room_id, messages, room_agents)
                    
                    # === Empty Response Guard ===
                    # 生成失敗やフィルタリングで空の応答が返ってきた場合、そのまま進むと無限ループになる
                    if not response or not response.strip():
                        st.warning(f"⚠️ {next_agent['name']} からの応答がありませんでした。スキップします。")
                        
                        # 次の走者をランダムに決定してリトライ
                        others = [a for a in active_agents if a['id'] != next_agent['id']]
                        if others:
                             import random
                             fallback = random.choice(others)
                             st.session_state[state_key] = fallback['id']
                        
                        time.sleep(1)
                        st.rerun()
                    
                    # === なりすまし切断 (Anti-Impersonation Cutoff) ===
                    # モデレーターが他人のロール（絵文字ヘッダー）を出し始めたら、そこから先は「乗っ取り」なので削除
                    # これをSavior Logicの前にやることで、タグが含まれていても消去し、Saviorに正しいタグを作らせる
                    if next_agent.get('category') == 'facilitation' or "モデレーター" in next_agent['name']:
                         # 改行後に他人の絵文字ヘッダーが来たらアウト
                         # 許可する絵文字: 🎤 (自分)
                         # 拒否する絵文字: 📝💡🔧🔍🧸📊📈🎲🎨 (他人)
                         # 改行直後にこれらが来たらアウトだが、文中ならOKとするため正規表現を厳格化
                         stop_pattern = r'\n\s*(\n|^)(📝|💡|🔧|🔍|🧸|📊|📈|🎲|🎨)'
                         imperson_match = re.search(stop_pattern, response)
                         if imperson_match:
                             response = response[:imperson_match.start()]
                     
                     # === モデレーター専用：独り相撲防止救済ロジック (The Savior) ===
                    # モデレーターがNEXTタグを忘れて「一人二役」を始めた場合、強制的に介入する
                    if next_agent.get('category') == 'facilitation' or "モデレーター" in next_agent['name']:
                        import random
                        
                        # 特例：文末に「📈 マーケター」のように、次の話者のアイコンと名前だけ置いて終わっている場合
                        # これを最強の指名シグナルとして優先する（IDタグよりも優先）
                        # 末尾50文字くらいを見る
                        tail_text = response[-50:].strip()
                        baton_match = re.search(r'(📝|💡|🔧|🔍|🧸|📊|📈|🎲|🎨)\s*([^\s]+)', tail_text)
                        
                        forced_target_id = None
                        if baton_match:
                            b_icon = baton_match.group(1)
                            b_name_part = baton_match.group(2) # 名前の一部
                            
                            # アイコン一致かつ名前部分一致を探す
                            for a in room_agents:
                                if a['icon'] == b_icon:
                                    # 名前もチェック
                                    if b_name_part in a['name']:
                                        forced_target_id = a['id']
                                        break
                            
                            if forced_target_id:
                                # タグがあろうとなかろうと、強制的にこいつにする
                                # 既存のタグがあれば消す
                                response = re.sub(r'\[\[NEXT:.*?\]\]', '', response)
                                response = response.strip() + f"\n\n[[NEXT: {forced_target_id}]]"
                                st.toast(f"🎯 バトンパス検知: {b_icon} {b_name_part} へ転送")
                                # これ以上何もしないでOK
                        
                        # バトンパスがなければ通常のチェックへ
                        if not forced_target_id:
                            # 1. 正常なNEXTタグまたは【指名】があるか確認
                            # どちらか早い方で切る
                            
                            next_tag_match = re.search(r'\[\[NEXT:\s*\[?(\d+)\]?\]?', response)
                            nomination_match = re.search(r'【指名】(.*?)(?:$|\n)', response)
                            
                            cutoff_index = -1
                            
                            if next_tag_match:
                                cutoff_index = next_tag_match.end()
                                # 閉じ括弧補完
                                if not response[:cutoff_index].strip().endswith("]]"):
                                     response = response[:cutoff_index] + "]]"
                                     cutoff_index = len(response)
                            
                            elif nomination_match:
                                cutoff_index = nomination_match.end()
                            
                            # FINISHタグがある場合は何もしない（優先）
                            if "[[FINISH]]" in response:
                                pass
                            
                            elif cutoff_index != -1:
                                # マッチした箇所で物理的に切断
                                response = response[:cutoff_index]
                            
                            else:
                                # 2. タグも指名もない場合 -> 強制カット＆モデレーター戻し
                                # 幻覚（次のヘッダー等）が出る前に切る
                                
                                # ヘッダーっぽいものがあればそこで切る
                                hallucination = re.search(r'(\n|^)(🎤|📈|# ペルソナ|Thinking|【).*', response[200:], re.DOTALL)
                                if hallucination:
                                    response = response[:200+hallucination.start()]
                                
                                # 安全策としてモデレーターへ戻すタグを付与
                                if is_moderator:
                                    # モデレーターが指名忘れた -> ランダム
                                    pass # 下流のAgentSchedulerに任せるのでタグなしでOK
                                else:
                                    # 専門家が指名忘れた -> モデレーターへ戻す
                                    response += f"\n\n[[NEXT: {mod_agent['id']}]]"
                                    st.toast("🛡️ 指名忘れを検知: モデレーターに戻します", icon="↩️")
                            # より柔軟な正規表現: "指名" や "Next" も拾う
                            pass_match = re.search(r'(?:【パス|【指名|Next)(?:：|:)\s*(.*?)(?:さん|へ|、|\]|\n|$)', response, re.IGNORECASE)
                            target_id = None
                            
                            if pass_match:
                                raw_target = pass_match.group(1).strip()
                                # ノイズ除去
                                target_name = re.sub(r'(さん|先生|担当|君|氏)', '', raw_target).strip()
                                
                                # 1. 名前での完全〜部分一致
                                for a in active_agents:
                                    if a['name'] == target_name: # 完全一致優先
                                        target_id = a['id']
                                        break
                                if not target_id:
                                    for a in active_agents:
                                        if target_name in a['name'] or a['name'] in target_name:
                                            target_id = a['id']
                                            break
                                
                                # 2. 役割(role)での検索 fallback
                                if not target_id:
                                    # "論理" -> "論理担当" / "ロジカル" -> "論理担当"
                                    for a in active_agents:
                                        if target_name in a['role'] or a['role'] in target_name:
                                            target_id = a['id']
                                            break
                                            
                                # 3. カテゴリでの検索 fallback (英語対応)
                                if not target_id:
                                     # data -> analyst, logic -> logic
                                     for a in active_agents:
                                         if target_name.lower() in a.get('category','').lower():
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
                        
                        # 1. 通常の議事録更新
                        auto_update_board(room_id, temp_msgs)
                        
                        # 2. 事後監査 (Systems Audit)
                        with st.status("🔍 システム監査を実行中...", expanded=True) as status:
                            st.write("論理整合性チェック中...")
                            audit = generate_audit_report(room_id, temp_msgs, room_agents)
                            st.write("監査レポート生成完了")
                            status.update(label="✅ 監査完了", state="complete", expanded=False)
                        
                        # IDの代わりに専用のシステム名で保存
                        db.add_message(room_id, "system", f"【監査レポート】\n{audit}")
                        
                        st.balloons()
                        st.toast("🏁 議論が終了しました。監査レポートを確認してください。", icon="🛑")
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
                    error_msg = str(e)
                    if "SAFETY" in error_msg or "400" in error_msg:
                        st.toast(f"⚠️ {next_agent['name']} の発言がAI安全フィルターによりブロックされました。", icon="🛡️")
                        # 無言で落ちると困るので、システムメッセージとして残すか、リトライするか
                        # ここでは一旦スキップして次へ（上のEmpty Response Guardで処理されるかもだが、Exceptionはここで捕捉）
                        time.sleep(1)
                        st.rerun()
                    else:
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
