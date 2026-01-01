"""
AI Teams - LLM Client Wrapper
各社APIの統一インターフェース（ストリーミング + マルチモーダル対応）
"""
import openai
import anthropic
import google.generativeai as genai
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')

from typing import List, Dict, Iterator, Optional
import base64
import json

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
    
    def _prepare_multimodal_content(self, messages: List[Dict], provider: str) -> List[Dict]:
        """マルチモーダルコンテンツの準備（プロバイダー別）"""
        processed_messages = []
        
        for msg in messages:
            # attachmentsがある場合は処理
            if msg.get('attachments'):
                try:
                    attachments = json.loads(msg['attachments']) if isinstance(msg['attachments'], str) else msg['attachments']
                    
                    if provider == "openai":
                        # OpenAI形式: content配列
                        content_parts = [{"type": "text", "text": msg['content']}]
                        for att in attachments:
                            if att['type'].startswith('image/'):
                                content_parts.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{att['type']};base64,{att['data']}"
                                    }
                                })
                        processed_messages.append({
                            "role": msg['role'],
                            "content": content_parts
                        })
                    
                    elif provider == "anthropic":
                        # Anthropic形式: content配列
                        content_parts = []
                        for att in attachments:
                            if att['type'].startswith('image/'):
                                # 画像タイプを変換
                                media_type = att['type']
                                content_parts.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": att['data']
                                    }
                                })
                        content_parts.append({"type": "text", "text": msg['content']})
                        processed_messages.append({
                            "role": msg['role'],
                            "content": content_parts
                        })
                    
                    elif provider == "google":
                        # Gemini形式: テキストに画像情報を追加
                        # 注: Geminiは別途処理が必要
                        processed_messages.append({
                            "role": msg['role'],
                            "content": msg['content'],
                            "attachments": attachments
                        })
                    
                except Exception as e:
                    # エラー時はテキストのみ
                    processed_messages.append({
                        "role": msg['role'],
                        "content": msg['content'] + f"\n[添付ファイル処理エラー: {e}]"
                    })
            else:
                # 添付なしの場合はそのまま
                processed_messages.append(msg)
        
        return processed_messages
    
    def generate_stream(self, provider: str, model: str, messages: List[Dict], extra_system_prompt: str = "") -> Iterator[str]:
        """ストリーミング生成（統一インターフェース）"""
        
        # extra_system_prompt の注入 (app.pyからの強制結合)
        current_messages = [m.copy() for m in messages] # Deep copy的に複製
        if extra_system_prompt:
            # 枠組みを付けて強化
            formatted_extra = f"""
【現在の戦況と絶対ルール】
{extra_system_prompt}
-------------------
"""
            system_found = False
            for m in current_messages:
                if m['role'] == 'system':
                    # 既存のシステムプロンプトの「前」に結合して最優先事項とする
                    m['content'] = f"{formatted_extra}\n\n{m['content']}"
                    system_found = True
                    break
            if not system_found:
                current_messages.insert(0, {"role": "system", "content": formatted_extra})

        # マルチモーダル対応
        processed_messages = self._prepare_multimodal_content(current_messages, provider)
        
        if provider == "openai":
            yield from self._openai_stream(model, processed_messages)
        elif provider == "google":
            yield from self._google_stream(model, processed_messages)
        elif provider == "anthropic":
            yield from self._anthropic_stream(model, processed_messages)
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
            
            # 画像がある場合は特別処理
            has_images = any(msg.get('attachments') for msg in messages)
            
            if has_images:
                # 最後のメッセージに画像がある場合
                last_msg = messages[-1]
                if last_msg.get('attachments'):
                    import PIL.Image
                    import io
                    
                    parts = [last_msg['content']]
                    for att in last_msg['attachments']:
                        if att['type'].startswith('image/'):
                            img_bytes = base64.b64decode(att['data'])
                            img = PIL.Image.open(io.BytesIO(img_bytes))
                            parts.append(img)
                    
                    response = model_instance.generate_content(parts, stream=True)
                else:
                    # メッセージ形式を変換
                    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                    response = model_instance.generate_content(prompt, stream=True)
            else:
                # メッセージ形式を変換
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                response = model_instance.generate_content(prompt, stream=True)
            
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
    
    def generate(self, provider: str, model: str, messages: List[Dict], extra_system_prompt: str = "") -> str:
        """非ストリーミング生成（後方互換性のため）"""
        result = ""
        for chunk in self.generate_stream(provider, model, messages, extra_system_prompt):
            result += chunk
        return result
