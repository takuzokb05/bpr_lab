import gradio as gr
import time
import json
import re
import traceback
from database import Database
from llm_client import LLMClient

# ==========================================
# 初期設定
# ==========================================

tmp_db = Database()

# APIキーの取得
try:
    with open("API_KEY.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    api_keys = {
        "google": lines[1].strip() if len(lines) > 1 else "",
        "openai": lines[4].strip() if len(lines) > 4 else "",
        "anthropic": lines[7].strip() if len(lines) > 7 else ""
    }
except FileNotFoundError:
    api_keys = tmp_db.get_api_keys()

llm_client = LLMClient(api_keys)

# ==========================================
# ヘルパー関数
# ==========================================

def get_room_choices():
    db = Database()
    rooms = db.get_all_rooms()
    return [(f"{r['title']}", r['id']) for r in rooms]

def get_agent_choices():
    db = Database()
    agents = db.get_all_agents()
    return [(f"{t[1]}", t[0]) for t in [(a['id'], f"{a['icon']} {a['name']}") for a in agents]]

agents = tmp_db.get_all_agents()
default_agent_ids = [a['id'] for a in agents if a['system_default'] == 1]

def format_chat_history(room_id):
    if not room_id:
        return []
    
    db = Database()
    messages = db.get_room_messages(room_id)
    history = []
    
    for msg in messages:
        if msg['role'] == 'user':
            history.append([msg['content'], None])
        else:
            agent_name = msg.get('agent_name', 'System')
            icon = msg.get('icon', '🤖')
            content = f"**{icon} {agent_name}**\n\n{msg['content']}"
            history.append([None, content])
            
    return history

def get_board_markdown(room_id):
    if not room_id:
        return "### 左側のメニューから会議を選択または作成してください"
        
    db = Database()
    room = db.get_room(room_id)
    if not room:
        return "ルームが見つかりません"
        
    try:
        content = json.loads(room['board_content'])
    except:
        return "議事録データなし"
    
    md = f"# 📋 議事録: {room['title']}\n---\n"
    
    if content.get('topic'):
        md += f"### テーマ: {content['topic']}\n\n"
        
    if content.get('agreements'):
        md += "### ✅ 合意事項\n"
        for i, item in enumerate(content['agreements'], 1):
            md += f"{i}. {item}\n"
        md += "\n"
            
    if content.get('concerns'):
        md += "### ⚠️ 懸念点\n"
        for i, item in enumerate(content['concerns'], 1):
            md += f"{i}. {item}\n"
        md += "\n"
            
    if content.get('next_actions'):
        md += "### 📝 ネクストアクション\n"
        for item in content['next_actions']:
            md += f"- [ ] {item}\n"
            
    if not any([content.get('agreements'), content.get('concerns'), content.get('next_actions'), content.get('topic')]):
        md += "*議論が進行するとここに議事録が自動生成されます*"
        
    return md

# ==========================================
# イベントハンドラ
# ==========================================

def on_room_select(room_id):
    history = format_chat_history(room_id)
    board = get_board_markdown(room_id)
    return history, board, room_id

def on_create_room(title, description, selected_agents):
    if not title:
        return gr.update(), "会議名を入力してください", None
    if not selected_agents:
        return gr.update(), "エージェントを少なくとも1人選択してください", None

    db = Database()
    room_id = db.create_room(title, description, selected_agents)
    new_choices = get_room_choices()
    history = format_chat_history(room_id)
    board = get_board_markdown(room_id)
    return gr.update(choices=new_choices, value=room_id), f"会議「{title}」を作成しました", room_id

def chat_process(user_message, room_id):
    if not room_id:
        yield [], get_board_markdown(None), "ルームを選択してください"
        return

    db = Database()
    db.add_message(room_id, "user", user_message)
    yield format_chat_history(room_id), get_board_markdown(room_id), "議論を開始します..."

    turn_count = 0
    phase = "opening"
    discussion_running = True
    
    room_agents = db.get_room_agents(room_id)
    if not room_agents:
        yield format_chat_history(room_id), get_board_markdown(room_id), "エージェントがいません"
        return

    while discussion_running and turn_count <= 16:
        next_agent = None
        if turn_count == 0:
            phase = "opening"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn_count == 1:
            phase = "divergence"
            idea_agent = next((a for a in room_agents if "アイデア" in a['name']), None)
            next_agent = idea_agent if idea_agent else room_agents[1 % len(room_agents)]
        elif turn_count <= 6:
            next_agent = room_agents[turn_count % len(room_agents)]
        elif turn_count == 7:
            phase = "convergence"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn_count <= 12:
            next_agent = room_agents[turn_count % len(room_agents)]
        elif turn_count == 13:
            phase = "conclusion"
            facilitator = next((a for a in room_agents if "モデレーター" in a['name'] or "司会" in a['name']), None)
            next_agent = facilitator if facilitator else room_agents[0]
        elif turn_count < 16:
            next_agent = room_agents[0]
        else:
            discussion_running = False
            next_agent = None

        if next_agent:
            yield format_chat_history(room_id), get_board_markdown(room_id), f"{next_agent['icon']} {next_agent['name']} が思考中... (フェーズ: {phase})"
            
            messages = db.get_room_messages(room_id)
            recent_messages = messages[-5:] if len(messages) > 5 else messages
            
            context = []
            for msg in recent_messages:
                # 3.x系ではGenerator内でState渡しが難しいかもしれないので、シンプルに動かす
                role = "user" if msg['role'] == "user" else "assistant"
                context.append({"role": role, "content": msg['content']})

            if "モデレーター" in next_agent['name'] or "司会" in next_agent['name']:
                system_prompt = f"あなたは{next_agent['name']}です。役割:{next_agent['role']}。フェーズ:{phase}。司会者として議論を整理してください。50文字以内。"
            else:
                system_prompt = f"あなたは{next_agent['name']}です。役割:{next_agent['role']}。フェーズ:{phase}。詳細に具体的に意見を述べてください。"

            full_context = [{"role": "system", "content": system_prompt}] + context
            
            try:
                response = llm_client.generate(next_agent['provider'], next_agent['model'], full_context)
                db.add_message(room_id, "assistant", response, next_agent['id'])
                turn_count += 1
                yield format_chat_history(room_id), get_board_markdown(room_id), f"ターン {turn_count}/16 完了"
                time.sleep(0.5)
            except Exception as e:
                traceback.print_exc()
                yield format_chat_history(room_id), get_board_markdown(room_id), f"エラー発生: {str(e)}"
                time.sleep(2)

    yield format_chat_history(room_id), get_board_markdown(room_id), "📝 書記AIが議事録を作成中..."
    
    scribe = next((a for a in room_agents if "書記" in a['name']), None)
    if scribe:
        try:
            all_messages = db.get_room_messages(room_id)
            discussion_text = "\n\n".join([f"[{msg.get('agent_name', 'ユーザー')}]: {msg['content']}" for msg in all_messages])
            
            scribe_prompt = "以下の議論を分析し、構造化された議事録を作成してください。必ずJSON形式で出力してください。"
            scribe_res = llm_client.generate(scribe['provider'], scribe['model'], [{"role": "system", "content": f"あなたは{scribe['name']}です。"}, {"role": "user", "content": f"{scribe_prompt}\n\n{discussion_text}"}])
            
            json_match = re.search(r'\{.*\}', scribe_res, re.DOTALL)
            if json_match:
                board_content = json.loads(json_match.group())
                db.update_room_board(room_id, board_content)
        except Exception as e:
            traceback.print_exc()

    yield format_chat_history(room_id), get_board_markdown(room_id), "✅ 議論完了"

# ==========================================
# UI構築
# ==========================================

with gr.Blocks(title="AI Teams", theme=gr.themes.Soft(), css="footer {visibility: hidden}") as demo:
    current_room_id = gr.State(value=None)
    gr.Markdown("# 🎤 AI Teams: Professional AI Discussion")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Accordion("📂 会議室管理", open=True):
                room_dropdown = gr.Dropdown(choices=get_room_choices(), label="会議室を選択", interactive=True)
                refresh_btn = gr.Button("🔄 リスト更新")
            with gr.Accordion("➕ 新規会議作成", open=False):
                new_room_title = gr.Textbox(label="会議名")
                new_room_desc = gr.Textbox(label="説明")
                # 3.x系でのCheckboxGroup対応
                # choicesはリストのリストまたはタプル。valueは値のリスト。
                new_room_agents = gr.CheckboxGroup(choices=get_agent_choices(), value=default_agent_ids, label="参加エージェント")
                create_btn = gr.Button("作成", variant="primary")
            with gr.Accordion("⚙️ 設定", open=False):
                gr.Markdown("APIキーは `API_KEY.txt` から読み込まれています。")

        with gr.Column(scale=2):
            # 3.x系のChatbotはタプル形式のみ。type引数は存在しない。
            chatbot = gr.Chatbot(height=800, label="チャットルーム")
            status_msg = gr.Markdown("待機中...")
            with gr.Row():
                msg_input = gr.Textbox(show_label=False, placeholder="議題やメッセージを入力...", scale=4)
                send_btn = gr.Button("🚀 送信", variant="primary", scale=1)

        with gr.Column(scale=1):
            gr.Markdown("### 📋 リアルタイム議事録")
            board_view = gr.Markdown("ルームを選択してください")

    room_dropdown.change(fn=on_room_select, inputs=[room_dropdown], outputs=[chatbot, board_view, current_room_id])
    refresh_btn.click(fn=lambda: gr.update(choices=get_room_choices()), outputs=[room_dropdown])
    create_btn.click(fn=on_create_room, inputs=[new_room_title, new_room_desc, new_room_agents], outputs=[room_dropdown, status_msg, current_room_id]).success(fn=on_room_select, inputs=[current_room_id], outputs=[chatbot, board_view, current_room_id])
    
    msg_input.submit(fn=chat_process, inputs=[msg_input, current_room_id], outputs=[chatbot, board_view, status_msg])
    # 3.x系では .then で lambda: "" を繋ぐと挙動が安定しないことがあるので、submitの戻り値で入力クリアは難しい。
    # しかしUX向上のため、msg_input.submitの後に text_area.update(value="") を返したい。
    # 3.xのsubmitはジェネレータと相性が悪い場合があるが、queue()を使えばいけるはず。
    
    # 送信ボタン
    send_btn.click(fn=chat_process, inputs=[msg_input, current_room_id], outputs=[chatbot, board_view, status_msg])

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=8506) # ポート8506で起動
