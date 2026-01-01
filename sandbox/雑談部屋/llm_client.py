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
